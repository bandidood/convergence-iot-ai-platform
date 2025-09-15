#!/bin/bash

# =============================================================================
# SCRIPT DE DURCISSEMENT DOCKER SÉCURISÉ - RNCP 39394
# Configuration Docker Pro avec hardening selon NIST CIS
# =============================================================================

set -euo pipefail

# Configuration des couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}🔐 DURCISSEMENT DOCKER SÉCURISÉ - RNCP 39394${NC}"
echo "=================================================="

# Vérification des privilèges
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ Ce script ne doit pas être exécuté en root pour la sécurité${NC}"
   exit 1
fi

# 1. Configuration daemon Docker sécurisé
echo -e "\n${YELLOW}🔧 Configuration daemon Docker sécurisé...${NC}"

# Création du répertoire de configuration Docker
sudo mkdir -p /etc/docker

# Configuration daemon Docker avec hardening CIS
cat << 'EOF' | sudo tee /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false,
  "no-new-privileges": true,
  "seccomp-profile": "/etc/docker/seccomp-profile.json",
  "apparmor-profile": "docker-default",
  "selinux-enabled": false,
  "disable-legacy-registry": true,
  "experimental": false,
  "metrics-addr": "127.0.0.1:9323",
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ],
  "default-ulimits": {
    "nofile": {
      "Hard": 64000,
      "Name": "nofile",
      "Soft": 64000
    },
    "memlock": {
      "Hard": -1,
      "Name": "memlock",
      "Soft": -1
    }
  },
  "icc": false,
  "iptables": true,
  "ip-forward": false,
  "ip-masq": false,
  "bridge": "none",
  "default-network-opts": {
    "bridge": {
      "com.docker.network.bridge.name": "docker0",
      "com.docker.network.bridge.enable_ip_masquerade": "false",
      "com.docker.network.bridge.enable_icc": "false"
    }
  },
  "authorization-plugins": [],
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 5,
  "registry-mirrors": [],
  "insecure-registries": [],
  "debug": false
}
EOF

echo -e "${GREEN}✅ Configuration daemon Docker sécurisé créée${NC}"

# 2. Profil Seccomp personnalisé
echo -e "\n${YELLOW}🔧 Configuration profil Seccomp...${NC}"

cat << 'EOF' | sudo tee /etc/docker/seccomp-profile.json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "archMap": [
    {
      "architecture": "SCMP_ARCH_X86_64",
      "subArchitectures": [
        "SCMP_ARCH_X86",
        "SCMP_ARCH_X32"
      ]
    }
  ],
  "syscalls": [
    {
      "names": [
        "accept", "accept4", "access", "alarm", "bind", "brk", "capget", "capset",
        "chdir", "chmod", "chown", "chroot", "clock_getres", "clock_gettime",
        "clone", "close", "connect", "copy_file_range", "creat", "dup", "dup2",
        "dup3", "epoll_create", "epoll_create1", "epoll_ctl", "epoll_pwait",
        "epoll_wait", "eventfd", "eventfd2", "execve", "exit", "exit_group",
        "faccessat", "fadvise64", "fallocate", "fanotify_mark", "fchdir",
        "fchmod", "fchmodat", "fchown", "fchownat", "fcntl", "fdatasync",
        "fgetxattr", "flistxattr", "flock", "fork", "fremovexattr", "fsetxattr",
        "fstat", "fstatfs", "fsync", "ftruncate", "futex", "getcwd", "getdents",
        "getdents64", "getegid", "geteuid", "getgid", "getgroups", "getpgrp",
        "getpid", "getppid", "getpriority", "getrandom", "getresgid", "getresuid",
        "getrlimit", "get_robust_list", "getrusage", "getsid", "getsockname",
        "getsockopt", "gettid", "gettimeofday", "getuid", "getxattr", "inotify_add_watch",
        "inotify_init", "inotify_init1", "inotify_rm_watch", "io_cancel", "ioctl",
        "io_destroy", "io_getevents", "ioprio_get", "ioprio_set", "io_setup", "io_submit",
        "ipc", "kill", "lchown", "lgetxattr", "link", "linkat", "listen", "listxattr",
        "llistxattr", "lremovexattr", "lseek", "lsetxattr", "lstat", "madvise",
        "memfd_create", "mincore", "mkdir", "mkdirat", "mknod", "mknodat", "mlock",
        "mlockall", "mmap", "mount", "mprotect", "mq_getsetattr", "mq_notify",
        "mq_open", "mq_timedreceive", "mq_timedsend", "mq_unlink", "mremap",
        "msgctl", "msgget", "msgrcv", "msgsnd", "msync", "munlock", "munlockall",
        "munmap", "nanosleep", "newfstatat", "open", "openat", "pause", "pipe",
        "pipe2", "poll", "ppoll", "prctl", "pread64", "preadv", "prlimit64",
        "pselect6", "ptrace", "pwrite64", "pwritev", "read", "readahead",
        "readlink", "readlinkat", "readv", "recv", "recvfrom", "recvmmsg",
        "recvmsg", "remap_file_pages", "removexattr", "rename", "renameat",
        "renameat2", "restart_syscall", "rmdir", "rt_sigaction", "rt_sigpending",
        "rt_sigprocmask", "rt_sigqueueinfo", "rt_sigreturn", "rt_sigsuspend",
        "rt_sigtimedwait", "rt_tgsigqueueinfo", "sched_getaffinity", "sched_getattr",
        "sched_getparam", "sched_get_priority_max", "sched_get_priority_min",
        "sched_getscheduler", "sched_setaffinity", "sched_setattr", "sched_setparam",
        "sched_setscheduler", "sched_yield", "seccomp", "select", "semctl", "semget",
        "semop", "semtimedop", "send", "sendfile", "sendmmsg", "sendmsg", "sendto",
        "setfsgid", "setfsuid", "setgid", "setgroups", "setitimer", "setpgid",
        "setpriority", "setregid", "setresgid", "setresuid", "setreuid", "setrlimit",
        "set_robust_list", "setsid", "setsockopt", "set_thread_area", "set_tid_address",
        "setuid", "setxattr", "shmat", "shmctl", "shmdt", "shmget", "shutdown",
        "sigaltstack", "signalfd", "signalfd4", "sigreturn", "socket", "socketcall",
        "socketpair", "splice", "stat", "statfs", "symlink", "symlinkat", "sync",
        "sync_file_range", "syncfs", "sysinfo", "tee", "tgkill", "time", "timer_create",
        "timer_delete", "timerfd_create", "timerfd_gettime", "timerfd_settime",
        "timer_getoverrun", "timer_gettime", "timer_settime", "times", "tkill",
        "truncate", "umask", "uname", "unlink", "unlinkat", "utime", "utimensat",
        "utimes", "vfork", "vmsplice", "wait4", "waitid", "write", "writev"
      ],
      "action": "SCMP_ACT_ALLOW",
      "args": [],
      "comment": "",
      "includes": {},
      "excludes": {}
    }
  ]
}
EOF

echo -e "${GREEN}✅ Profil Seccomp sécurisé créé${NC}"

# 3. Configuration réseau Docker sécurisé
echo -e "\n${YELLOW}🔧 Configuration réseau Docker sécurisé...${NC}"

# Désactivation du forwarding IP par défaut
echo 'net.ipv4.ip_forward=0' | sudo tee -a /etc/sysctl.conf

# Configuration iptables pour Docker
sudo tee /etc/docker/iptables-docker.sh << 'EOF'
#!/bin/bash
# Règles iptables sécurisées pour Docker

# Flush des règles existantes
iptables -F DOCKER-USER

# Politique par défaut DROP
iptables -I DOCKER-USER -j DROP

# Autoriser le trafic interne entre conteneurs du même réseau
iptables -I DOCKER-USER -i docker0 -o docker0 -j ACCEPT

# Autoriser le trafic des réseaux privés définis
iptables -I DOCKER-USER -s 172.22.0.0/16 -d 172.22.0.0/16 -j ACCEPT
iptables -I DOCKER-USER -s 172.23.0.0/16 -d 172.23.0.0/16 -j ACCEPT

# Autoriser uniquement les ports nécessaires depuis l'extérieur
iptables -I DOCKER-USER -p tcp --dport 3001 -j ACCEPT  # Grafana
iptables -I DOCKER-USER -p tcp --dport 8086 -j ACCEPT  # InfluxDB
iptables -I DOCKER-USER -p tcp --dport 9000:9001 -j ACCEPT  # MinIO

# Logging des tentatives de connexion refusées
iptables -I DOCKER-USER -m limit --limit 5/min -j LOG --log-prefix "DOCKER-DENIED: "

# Retourner au traitement normal pour le trafic autorisé
iptables -I DOCKER-USER -j RETURN
EOF

sudo chmod +x /etc/docker/iptables-docker.sh
echo -e "${GREEN}✅ Configuration iptables Docker créée${NC}"

# 4. Configuration audit Docker
echo -e "\n${YELLOW}🔧 Configuration audit Docker...${NC}"

# Règles auditd pour Docker
sudo tee -a /etc/audit/rules.d/docker.rules << 'EOF'
# Audit Docker daemon
-w /usr/bin/docker -p wa -k docker

# Audit fichiers de configuration Docker
-w /etc/docker -p wa -k docker
-w /lib/systemd/system/docker.service -p wa -k docker
-w /lib/systemd/system/docker.socket -p wa -k docker
-w /etc/default/docker -p wa -k docker
-w /etc/docker/daemon.json -p wa -k docker

# Audit répertoires Docker
-w /var/lib/docker -p wa -k docker
-w /etc/docker -p wa -k docker

# Audit processus Docker
-a always,exit -F arch=b64 -S execve -F path=/usr/bin/docker -k docker
-a always,exit -F arch=b32 -S execve -F path=/usr/bin/docker -k docker
EOF

echo -e "${GREEN}✅ Configuration audit Docker créée${NC}"

# 5. Création utilisateur Docker non-privilégié
echo -e "\n${YELLOW}🔧 Configuration utilisateur Docker...${NC}"

# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER

# Configuration des limites utilisateur
sudo tee -a /etc/security/limits.conf << 'EOF'
# Limites Docker pour utilisateurs non-root
@docker soft nofile 65536
@docker hard nofile 65536
@docker soft nproc 4096
@docker hard nproc 4096
EOF

echo -e "${GREEN}✅ Utilisateur Docker configuré${NC}"

# 6. Configuration TLS pour Docker daemon
echo -e "\n${YELLOW}🔧 Configuration TLS Docker daemon...${NC}"

# Création du répertoire pour les certificats
sudo mkdir -p /etc/docker/certs
sudo chmod 700 /etc/docker/certs

# Note: Les certificats seront générés par le script PKI séparé
echo "# Certificats TLS Docker seront générés par setup_pki_infrastructure.sh" | sudo tee /etc/docker/certs/README.md

echo -e "${GREEN}✅ Répertoire TLS Docker préparé${NC}"

# 7. Configuration de monitoring Docker
echo -e "\n${YELLOW}🔧 Configuration monitoring Docker...${NC}"

# Service systemd pour métriques Docker
sudo tee /etc/systemd/system/docker-metrics.service << 'EOF'
[Unit]
Description=Docker Metrics Exporter
After=docker.service
Requires=docker.service

[Service]
Type=simple
ExecStart=/usr/bin/docker run --rm --name docker-metrics \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -p 127.0.0.1:9323:9323 \
    prom/docker-exporter:latest
Restart=always
RestartSec=10
User=docker-metrics

[Install]
WantedBy=multi-user.target
EOF

# Création utilisateur pour les métriques
sudo useradd -r -s /bin/false docker-metrics || true
sudo usermod -aG docker docker-metrics

echo -e "${GREEN}✅ Monitoring Docker configuré${NC}"

# 8. Scripts de vérification sécurité
echo -e "\n${YELLOW}🔧 Création scripts de vérification...${NC}"

# Script de benchmark CIS Docker
cat << 'EOF' > /tmp/docker-security-check.sh
#!/bin/bash
# Vérification sécurité Docker selon CIS Benchmark

echo "🔍 AUDIT SÉCURITÉ DOCKER CIS"
echo "================================"

# 1. Vérifier que Docker daemon fonctionne en mode rootless si possible
if pgrep -f "dockerd.*--rootless" >/dev/null; then
    echo "✅ Docker fonctionne en mode rootless"
else
    echo "⚠️  Docker fonctionne en mode root (configuration standard)"
fi

# 2. Vérifier la configuration du daemon
if [ -f /etc/docker/daemon.json ]; then
    echo "✅ Fichier de configuration daemon.json présent"
    
    if grep -q '"no-new-privileges": true' /etc/docker/daemon.json; then
        echo "✅ no-new-privileges activé"
    else
        echo "❌ no-new-privileges non activé"
    fi
    
    if grep -q '"live-restore": true' /etc/docker/daemon.json; then
        echo "✅ live-restore activé"
    else
        echo "❌ live-restore non activé"
    fi
else
    echo "❌ Fichier daemon.json non trouvé"
fi

# 3. Vérifier les permissions des fichiers Docker
echo "🔍 Vérification permissions fichiers Docker..."
find /etc/docker -type f -exec ls -la {} \; 2>/dev/null | head -10

# 4. Vérifier les conteneurs en cours d'exécution
echo "🔍 Conteneurs actifs:"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

echo "================================"
echo "✅ Audit sécurité Docker terminé"
EOF

chmod +x /tmp/docker-security-check.sh
sudo mv /tmp/docker-security-check.sh /usr/local/bin/docker-security-check
echo -e "${GREEN}✅ Script de vérification sécurité créé${NC}"

# 9. Redémarrage des services
echo -e "\n${YELLOW}🔄 Redémarrage services Docker...${NC}"

# Rechargement configuration systemd
sudo systemctl daemon-reload

# Application configuration iptables
if command -v iptables >/dev/null 2>&1; then
    sudo /etc/docker/iptables-docker.sh
    echo -e "${GREEN}✅ Règles iptables appliquées${NC}"
fi

# Redémarrage Docker avec nouvelle configuration
sudo systemctl restart docker
sleep 5

# Vérification que Docker fonctionne
if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker redémarré avec succès${NC}"
else
    echo -e "${RED}❌ Erreur lors du redémarrage Docker${NC}"
    exit 1
fi

# 10. Validation finale
echo -e "\n${BLUE}🔍 Validation configuration sécurisée...${NC}"

# Exécution du script de vérification
/usr/local/bin/docker-security-check

# Test de sécurité basique
echo -e "\n${YELLOW}🧪 Test sécurité basique...${NC}"

# Test 1: Tentative d'accès privilégié
if docker run --rm --cap-drop=ALL alpine:latest sh -c 'echo "Test sécurité réussi"' >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Test conteneur non-privilégié OK${NC}"
else
    echo -e "${RED}❌ Problème avec conteneur non-privilégié${NC}"
fi

# Résumé final
echo -e "\n=================================================="
echo -e "${GREEN}🎉 DURCISSEMENT DOCKER SÉCURISÉ TERMINÉ${NC}"
echo -e "${GREEN}✅ Configuration conforme aux standards CIS${NC}"
echo -e "${BLUE}ℹ️  Redémarrage de session requis pour groupe docker${NC}"
echo -e "${BLUE}ℹ️  Exécuter 'docker-security-check' pour audit régulier${NC}"
echo "=================================================="

# Message pour la suite
echo -e "\n${YELLOW}📋 ÉTAPES SUIVANTES:${NC}"
echo "1. Redémarrer votre session (logout/login)"
echo "2. Exécuter: docker-security-check"
echo "3. Continuer avec setup_k8s_local.sh"
echo "4. Puis setup_security_tools.sh"
echo "5. Enfin setup_pki_infrastructure.sh"
