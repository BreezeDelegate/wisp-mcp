FROM docker.io/nginxinc/nginx-unprivileged@sha256:e88d990b349df8cf4aa82f16642d7a23375016638c9ace4e5c6ca25028e62e65
COPY --chmod=0444 deploy/site/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --chmod=0555 docs/ /usr/share/nginx/html/
EXPOSE 8080
