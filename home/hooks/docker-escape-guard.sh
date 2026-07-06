#!/usr/bin/env bash
# PreToolUse Bash — Gate 0: deny docker container-escape / host-exposure invocations.
#
# Purpose:
#   Block docker run/create (and docker compose run/create) commands that carry flags
#   or volume mounts known to enable container escape or sensitive host data exposure,
#   BEFORE a rootless docker socket is enabled.  This is the keystone "Gate 0" control
#   in the layered security model.
#
# What it DENIES:
#   --privileged (full host access)
#   --device (host device passthrough)
#   --cap-add with: SYS_ADMIN, SYS_PTRACE, SYS_MODULE, DAC_READ_SEARCH, ALL
#   --security-opt apparmor=unconfined or seccomp=unconfined
#   --pid=host, --ipc=host, --uts=host, --userns=host, --cgroupns=host
#   --network=host / --net=host
#   Volume/mount of docker.sock (any path)
#   Volume/mount whose source resolves to /, $HOME, or known sensitive dirs/files
#   Relative volume source containing '..' (fail-closed on traversal)
#   docker compose down/rm with -v/--volumes (data destruction)
#
# What it also handles:
#   Clustered short flags containing v (e.g. -itv /:/host, -dv ~/.ssh:/s)
#
# Known limitations:
#   - Best-effort whitespace tokenizer; quoted paths containing spaces may slip through.
#   - Deny-specific tripwire: unenumerated escape vectors fail-OPEN by design (except
#     within the docker-run family where unparseable volume sources fail-CLOSED).
#   - A literal "docker run --privileged" inside a git commit message or string argument
#     is a known acceptable false-positive.
#   - Does not eval variables ($VAR in a volume path is not expanded).
#   - Cluster flag parsing assumes 'v' is the first value-taking flag in the cluster;
#     rare forms like -ev (where e also takes a value) are handled fail-CLOSED.

INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

deny() {
    jq -n --arg reason "$1" \
        '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason}}'
    exit 0
}

# clean_tok: strip leading/trailing shell meta-characters; expand ~ to $HOME
clean_tok() {
    local t="$1"
    t=$(printf '%s' "$t" | sed "s/^\`//; s/^(//; s/^\"//; s/^'//; s/[;|&)'\")\`]*\$//")
    case "$t" in
        "~/"*) t="$HOME${t#\~}" ;;
        "~")   t="$HOME" ;;
    esac
    printf '%s' "$t"
}

# extract_flag_val: given current token and next token, set EXTRACTED_VAL and ADV.
#   --flag=value  → EXTRACTED_VAL="${tok#*=}", ADV=0 (next token not consumed)
#   --flag value  → EXTRACTED_VAL="$ntok",    ADV=1 (next token consumed)
EXTRACTED_VAL="" ADV=0
extract_flag_val() {
    EXTRACTED_VAL="" ADV=0
    case "$1" in
        *=*) EXTRACTED_VAL="${1#*=}" ;;
        *)   EXTRACTED_VAL="$2"; ADV=1 ;;
    esac
}

# normalize_path: collapse //, remove /./, resolve /../ textually, strip trailing /
normalize_path() {
    local p="$1"
    case "$p" in "~/"*) p="$HOME${p#\~}" ;; "~") p="$HOME" ;; esac
    local c=1
    while [ $c -eq 1 ]; do
        c=0
        case "$p" in *//*) p=$(printf '%s' "$p" | sed 's|//|/|g'); c=1 ;; esac
        case "$p" in */./*|*/.) p=$(printf '%s' "$p" | sed 's|/\./|/|g; s|/\.$||'); c=1 ;; esac
    done
    c=1
    while [ $c -eq 1 ]; do
        c=0
        case "$p" in
            */../*|*/..) p=$(printf '%s' "$p" | sed 's|/[^/]*/\.\./|/|g; s|/[^/]*/\.\.$||'); c=1 ;;
        esac
    done
    case "$p" in /) : ;; *) p="${p%/}" ;; esac
    printf '%s' "$p"
}

# ---------------------------------------------------------------------------
# Sensitive path inventory (REAL paths)
# ---------------------------------------------------------------------------
H="$HOME"

# SENS_DIRS: deny exact, ancestors (SRC is parent of dir), and descendants (SRC is under dir)
SENS_DIRS=(
    "$H/.ssh"
    "$H/.gnupg"
    "$H/.aws"
    "$H/.docker"
    "$H/.kube"
    "$H/.config/gh"
    "$H/.config/google-chrome"
    "$H/.config/chromium"
    "$H/.mozilla"
    "$H/.password-store"
    "$H/.claude"
    "/root"
)

# SENS_FILES: deny exact match or if SRC is an ancestor (mounts the parent dir)
SENS_FILES=(
    "$H/.netrc"
    "$H/.pgpass"
    "$H/.git-credentials"
    "$H/.npmrc"
    "$H/.pypirc"
    "/etc/shadow"
    "/etc/passwd"
    "/etc/sudoers"
    "/var/run/docker.sock"
    "/run/docker.sock"
    "/run/user/1000/docker.sock"
)

# BROAD: deny exact or if SRC is an ancestor (but NOT descendants — a specific
# benign subpath under a BROAD entry is allowed through)
BROAD=(
    "/etc"
)

# check_sensitive: returns 0 (deny) or 1 (allow)
check_sensitive() {
    local SRC="$1"

    # Root and home are always denied
    [ "$SRC" = "/" ] && return 0
    [ "$SRC" = "$H" ] && return 0

    # SENS_DIRS: exact, SRC is ancestor (dir is under SRC), or SRC is descendant of dir
    local dir
    for dir in "${SENS_DIRS[@]}"; do
        [ "$SRC" = "$dir" ] && return 0
        case "$dir/" in "$SRC"/*) return 0 ;; esac   # dir is under SRC → SRC is broad ancestor
        case "$SRC/" in "$dir"/*) return 0 ;; esac   # SRC is under dir → descendant
    done

    # SENS_FILES: exact match or SRC is an ancestor of the file
    local f
    for f in "${SENS_FILES[@]}"; do
        [ "$SRC" = "$f" ] && return 0
        case "$f" in "$SRC"/*) return 0 ;; esac       # SRC is parent dir of file
    done

    # BROAD: exact match or SRC is an ancestor (NOT descendants)
    local b
    for b in "${BROAD[@]}"; do
        [ "$SRC" = "$b" ] && return 0
        case "$b" in "$SRC"/*) return 0 ;; esac       # b is under SRC → SRC is ancestor
    done

    return 1
}

# expand_home: expand a leading literal $HOME / ${HOME} in a path string.
#   The hook sees the raw command text, so a volume source written as
#   "$HOME/.claude" arrives un-expanded — without this it looks "relative" and
#   slips the absolute-path sensitivity check. Only $HOME is expanded (the one
#   shell var that maps onto sensitive paths); other vars remain a documented residual.
expand_home() {
    local p="$1" rest
    case "$p" in
        '$HOME'|'$HOME/'*)     rest=${p#'$HOME'};     printf '%s' "$HOME$rest" ;;
        '${HOME}'|'${HOME}/'*) rest=${p#'${HOME}'};   printf '%s' "$HOME$rest" ;;
        *)                     printf '%s' "$p" ;;
    esac
}

# check_v_value: evaluate a single -v / --volume value string.
#   Sets DENY_RESULT if the mount is dangerous; leaves it empty to allow.
#   Does NOT touch k or ADV — caller owns flow control.
check_v_value() {
    local vol_val="$1"

    # docker.sock anywhere in value → escape via Docker API
    case "$vol_val" in
        *docker.sock*)
            DENY_RESULT="Volume mounts Docker socket ('$vol_val'): grants full Docker API access = container escape."
            return
            ;;
    esac

    # Parse SRC (before first colon); no colon → named/anonymous volume → skip
    case "$vol_val" in
        *:*) src_raw="${vol_val%%:*}" ;;
        *)   return ;;
    esac

    # Strip surrounding quotes from SRC
    src_raw=$(printf '%s' "$src_raw" | sed "s/^['\"]//; s/['\"]$//")
    # Expand a leading literal $HOME / ${HOME} so it is checked as an absolute path
    src_raw=$(expand_home "$src_raw")

    case "$src_raw" in
        /*)
            # Absolute path → normalize and check
            norm_src=$(normalize_path "$src_raw")
            if check_sensitive "$norm_src"; then
                DENY_RESULT="Volume mounts sensitive host path '$norm_src' into the container."
            fi
            ;;
        *..*)
            # Relative with '..' → fail-closed (cannot safely resolve without cwd)
            DENY_RESULT="Relative volume source '$src_raw' contains '..' path traversal — denied (fail-closed)."
            ;;
        *)
            # Relative without '..' → project-local, allow
            ;;
    esac
}

# ---------------------------------------------------------------------------
# Tokenize
# ---------------------------------------------------------------------------
read -r -a TOKENS <<< "$CMD"
n=${#TOKENS[@]}

DENY_RESULT=""

# ---------------------------------------------------------------------------
# Main loop: process EVERY docker/podman occurrence in the token stream.
# This handles "cmd && docker run ..." patterns correctly.
# ---------------------------------------------------------------------------
i=0
while [ $i -lt $n ]; do
    raw_tok="${TOKENS[$i]}"
    tok=$(clean_tok "$raw_tok")

    # Match docker/podman (possibly path-prefixed, e.g. /usr/bin/docker)
    is_docker=0
    case "$tok" in
        docker|*/docker|podman|*/podman|docker-compose|*/docker-compose) is_docker=1 ;;
    esac

    if [ $is_docker -eq 0 ]; then i=$((i+1)); continue; fi

    # Handle legacy docker-compose binary
    compose=0
    case "$tok" in docker-compose|*/docker-compose) compose=1 ;; esac

    # --- Step 1: walk tokens to find the subcommand ---
    j=$((i+1))
    run_start=-1
    compose_destruct=0

    while [ $j -lt $n ]; do
        stok=$(clean_tok "${TOKENS[$j]}")
        case "$stok" in
            # Global docker flags that consume a value → skip 2 tokens
            --context|--host|-H|--config|--log-level|-l|--tlscacert|--tlscert|--tlskey)
                j=$((j+2)); continue ;;
            # 'compose' sub-token (from "docker compose ...")
            compose)
                compose=1; j=$((j+1)); continue ;;
            # Subcommands that launch a container
            run|create)
                run_start=$((j+1)); break ;;
            # Destructive compose subcommands
            down|rm)
                if [ $compose -eq 1 ]; then compose_destruct=1; fi
                break ;;
            # Any other flag → skip 1 (single-value or boolean)
            -*) j=$((j+1)); continue ;;
            # Any other word → some other subcommand (ps, images, pull, …)
            *) break ;;
        esac
        j=$((j+1))
    done

    # --- Step 4: compose down/rm + -v/--volumes → data destruction ---
    if [ $compose_destruct -eq 1 ]; then
        k=$((i+1))
        while [ $k -lt $n ]; do
            vtok=$(clean_tok "${TOKENS[$k]}")
            case "$vtok" in
                -v|--volumes)
                    DENY_RESULT="docker compose down/rm with -v/--volumes removes named volumes (data destruction risk)."
                    ;;
            esac
            k=$((k+1))
        done
        [ -n "$DENY_RESULT" ] && break
    fi

    [ -n "$DENY_RESULT" ] && break

    # No run/create subcommand found → nothing to scan for this docker occurrence
    if [ $run_start -eq -1 ]; then i=$((i+1)); continue; fi

    # --- Steps 2 & 3: scan flags from run_start ---
    k=$run_start
    while [ $k -lt $n ]; do
        ADV=0   # reset per-iteration; arms that consume a next token set ADV=1
        ftok=$(clean_tok "${TOKENS[$k]}")
        ntok=""
        [ $((k+1)) -lt $n ] && ntok=$(clean_tok "${TOKENS[$((k+1))]}")

        # Derive flag name (strip value after first =)
        case "$ftok" in *=*) flag_name="${ftok%%=*}" ;; *) flag_name="$ftok" ;; esac

        case "$flag_name" in

            # --privileged: boolean flag — standalone means true; only =false skips
            --privileged)
                case "$ftok" in
                    *=*)
                        priv_val="${ftok#*=}"
                        case "$priv_val" in
                            ""|true)
                                DENY_RESULT="--privileged grants full host capabilities to the container (escape vector)."
                                ;;
                        esac
                        ;;
                    *)
                        DENY_RESULT="--privileged grants full host capabilities to the container (escape vector)."
                        ;;
                esac
                [ -n "$DENY_RESULT" ] && break
                k=$((k+1)); continue ;;

            # --device: host device passthrough
            --device)
                DENY_RESULT="--device passes a host device into the container, which can enable escape (e.g. block device access)."
                break ;;

            # --cap-add: dangerous capabilities
            --cap-add)
                extract_flag_val "$ftok" "$ntok"
                # Normalize: strip optional CAP_ prefix, uppercase
                cap=$(printf '%s' "$EXTRACTED_VAL" | sed 's/^[Cc][Aa][Pp]_//' | tr '[:lower:]' '[:upper:]')
                case "$cap" in
                    SYS_ADMIN|SYS_PTRACE|SYS_MODULE|DAC_READ_SEARCH|ALL)
                        DENY_RESULT="--cap-add $cap grants a dangerous Linux capability (container escape / host inspection vector)."
                        ;;
                esac
                [ -n "$DENY_RESULT" ] && break
                k=$((k+ADV+1)); continue ;;

            # --security-opt: MAC disable
            --security-opt)
                extract_flag_val "$ftok" "$ntok"
                case "$EXTRACTED_VAL" in
                    *apparmor=unconfined*|*seccomp=unconfined*)
                        DENY_RESULT="--security-opt '$EXTRACTED_VAL' disables mandatory access controls (AppArmor/seccomp) on the container."
                        ;;
                esac
                [ -n "$DENY_RESULT" ] && break
                k=$((k+ADV+1)); continue ;;

            # --pid / --ipc / --uts / --userns / --cgroupns: host namespace sharing
            --pid|--ipc|--uts|--userns|--cgroupns)
                extract_flag_val "$ftok" "$ntok"
                case "$EXTRACTED_VAL" in
                    host)
                        DENY_RESULT="${flag_name}=host shares the host's ${flag_name#--} namespace with the container (escape vector)."
                        ;;
                esac
                [ -n "$DENY_RESULT" ] && break
                k=$((k+ADV+1)); continue ;;

            # --network / --net: host network
            --network|--net)
                extract_flag_val "$ftok" "$ntok"
                case "$EXTRACTED_VAL" in
                    host)
                        DENY_RESULT="--network=host shares the host network stack with the container."
                        ;;
                esac
                [ -n "$DENY_RESULT" ] && break
                k=$((k+ADV+1)); continue ;;

            # -v / --volume: host path mount
            -v|--volume)
                extract_flag_val "$ftok" "$ntok"
                check_v_value "$EXTRACTED_VAL"
                [ -n "$DENY_RESULT" ] && break
                k=$((k+ADV+1)); continue ;;

            # Clustered short flags (e.g. -itv, -dv, -tv).
            # Among Docker's single-letter short flags, only -v takes a value that is
            # an escape vector; all others (-i, -t, -d, -p, -e, etc.) are safe to skip.
            # Per pflag semantics: the first value-taking flag in the cluster consumes
            # either the remainder of the cluster string or the next token.
            -[a-zA-Z]*)
                # Skip if token contains '=' (not a bare cluster)
                case "$ftok" in
                    *=*) k=$((k+1)); continue ;;
                esac
                # Only care if the cluster contains 'v'
                case "$ftok" in
                    *v*)
                        rest="${ftok#-}"        # strip leading -
                        after="${rest#*v}"      # everything after the first 'v'
                        if [ -n "$after" ]; then
                            # v is not the last char; value is the rest of the cluster
                            check_v_value "$after"
                        else
                            # v is last; value is the next token
                            check_v_value "$ntok"
                            ADV=1
                        fi
                        [ -n "$DENY_RESULT" ] && break
                        ;;
                esac
                k=$((k+ADV+1)); continue ;;

            # --mount: bind/volume mount (comma-separated key=value)
            --mount)
                extract_flag_val "$ftok" "$ntok"
                mount_val="$EXTRACTED_VAL"

                # docker.sock anywhere in value
                case "$mount_val" in
                    *docker.sock*)
                        DENY_RESULT="--mount contains Docker socket path ('$mount_val'): grants full Docker API access = escape."
                        break
                        ;;
                esac

                # Parse source= or src= field from comma-list
                mount_src=""
                IFS_SAVE="$IFS"; IFS=","
                read -r -a mparts <<< "$mount_val"
                IFS="$IFS_SAVE"
                for part in "${mparts[@]}"; do
                    case "$part" in
                        source=*) mount_src="${part#source=}" ;;
                        src=*)    mount_src="${part#src=}" ;;
                    esac
                done

                if [ -n "$mount_src" ]; then
                    mount_src=$(printf '%s' "$mount_src" | sed "s/^['\"]//; s/['\"]$//")
                    mount_src=$(expand_home "$mount_src")
                    case "$mount_src" in
                        /*)
                            norm_ms=$(normalize_path "$mount_src")
                            if check_sensitive "$norm_ms"; then
                                DENY_RESULT="--mount binds sensitive host path '$norm_ms' into the container."
                            fi
                            [ -n "$DENY_RESULT" ] && break
                            ;;
                        *..*)
                            DENY_RESULT="--mount source '$mount_src' contains '..' path traversal — denied (fail-closed)."
                            break
                            ;;
                    esac
                fi
                k=$((k+ADV+1)); continue ;;

        esac
        k=$((k+1))
    done

    [ -n "$DENY_RESULT" ] && break
    i=$((i+1))
done

if [ -n "$DENY_RESULT" ]; then
    deny "$DENY_RESULT"
fi

# No escape vector found — allow (fail-open for unenumerated vectors)
exit 0

# ===========================================================================
# USER LIVE-VERIFY (run in a real sandboxed session after install + bless)
# ===========================================================================
#
# All of the following should be DENIED by this hook:
#
#   docker run -v ~/.ssh:/s alpine cat /s/id_rsa
#   docker run -v ~/.claude:/m alpine ls /m
#   docker run -v /etc/shadow:/m alpine cat /m
#   docker run -v /etc:/host/etc alpine cat /host/etc/passwd
#   docker run -v /:/host alpine chroot /host id
#   docker run -v ~/:/home alpine ls /home
#   docker run -v /var/run/docker.sock:/var/run/docker.sock alpine sh
#   docker run -v /run/docker.sock:/run/docker.sock alpine sh
#   docker run --privileged alpine id
#   docker run --privileged=true alpine id
#   docker run --device /dev/sda alpine fdisk /dev/sda
#   docker run --cap-add SYS_ADMIN alpine
#   docker run --cap-add=CAP_SYS_PTRACE alpine
#   docker run --cap-add cap_sys_admin alpine
#   docker run --cap-add ALL alpine
#   docker run --security-opt apparmor=unconfined alpine
#   docker run --security-opt=seccomp=unconfined alpine
#   docker run --pid=host alpine ps aux
#   docker run --pid host alpine ps aux
#   docker run --userns=host alpine
#   docker run --ipc=host alpine
#   docker run --net=host alpine
#   docker run --network host alpine
#   docker run --mount type=bind,source=/etc,target=/host/etc alpine
#   docker run --mount type=bind,source=/root/.ssh,target=/s alpine
#   docker run -v ../../../etc:/h alpine
#   docker compose down -v
#   docker compose down --volumes
#   timeout 5 docker run --privileged alpine
#   foo && docker run -v /etc/passwd:/p alpine
#   docker compose run --privileged web
#   docker run -itv /:/host alpine               (clustered -v, root mount)
#   docker run -dv ~/.ssh:/s alpine              (clustered -v, sensitive dir)
#   docker run -itv ../../etc:/h alpine          (clustered -v, relative traversal)
#
# All of the following should be ALLOWED by this hook:
#
#   docker run --rm -it alpine sh
#   docker run --cap-add NET_BIND_SERVICE alpine
#   docker run -v /tmp/myproj:/app node npm test
#   docker run -v mydata:/data postgres
#   docker run -p 8080:80 nginx
#   docker run -v ./src:/app node
#   docker ps
#   docker compose up -d
#   docker compose down
#   docker run --privileged=false alpine
#   docker run --mount type=bind,source=/etc/nginx/nginx.conf,target=/etc/nginx/nginx.conf:ro alpine
#   docker run -it alpine sh                     (clustered flags, no v)
#   docker run -vit alpine                       (v first in cluster, value "it" = named volume)
#   docker run -itv /tmp/proj:/app node          (clustered -v, non-sensitive abs path)
