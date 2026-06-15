#### Install Scruby-FTS

```shell
# For Scruby version 0
uv add "scruby-fts>=0.10.0,<1.0.0"
# For Scruby version 1
uv add "scruby-fts>=1.0.0,<2.0.0"
# For Scruby version 2
uv add "scruby-fts>=2.0.0,<3.0.0"
```

#### Install Manticore Search

For more information, see the <a href="https://manticoresearch.com/install/" alt="Install">documentation</a>.

##### Fedora 42 or later

```shell
# Install the repository:
sudo tee /etc/yum.repos.d/manticore.repo << "EOF" > /dev/null
[manticore]
name=Manticore Repository
baseurl=http://repo.manticoresearch.com/repository/manticoresearch/release/centos/10/$basearch
gpgcheck=1
enabled=1
gpgkey=https://repo.manticoresearch.com/GPG-KEY-SHA256-manticore
EOF

# Install Manticore Search:
sudo dnf install manticore manticore-extra
# Install English, German, and Russian lemmatizers:
sudo dnf install manticore-language-packs

# Run Manticore Search:
sudo systemctl start manticore
sudo systemctl enable manticore
sudo systemctl status manticore --no-pager -l

# HINT:
# ------------------------------------------------------------------------------
# Commands:
sudo systemctl start manticore
sudo systemctl restart manticore
sudo systemctl stop manticore
sudo systemctl enable manticore
sudo systemctl is-enabled manticore
sudo systemctl disable manticore
sudo systemctl status manticore --no-pager -l
sudo systemctl daemon-reload
sudo journalctl -u manticore

# Remove Manticore Search:
sudo systemctl stop manticore
sudo systemctl disable manticore
sudo dnf erase $(rpm -qa | grep manticore)
sudo rm -f /etc/yum.repos.d/manticore.repo
sudo rm -r /var/log/manticore /var/lib/manticore /var/run/manticore
sudo dnf makecache --refresh
```
