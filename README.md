# sr-rules — 个人 Shadowrocket 分流配置

自托管版：规则集在自己仓库里，由 GitHub Actions 每日从 v2fly 同步构建，不引用任何陌生人的远程表。

## 数据来源

- 规则集源自 v2fly/domain-list-community（dlc.dat），build.py 解析后生成 Shadowrocket 的 RULE-SET 列表。
- SyncRulesets 工作流每日自动运行，有变化才提交。

## 规则集

- Private.list：局域网域名 + 私网 IP 段 → DIRECT
- AI.list：AI 服务（category-ai-chat-!cn + 核心域名）→ US 组（锁美国出口）
- Telegram.list：Telegram 域名 + 官方 IP 段 → PROXY 组
- Direct.list：geolocation-cn → DIRECT
- Proxy.list：geolocation-!cn → PROXY 组
- 兜底：GEOIP CN 直连，其余全走 PROXY 组。

## 分组

- PROXY（fallback）：优先 Seattle，延迟劣化/断连自动切 Cloady，每 300 秒测一次。
- US（select）：手动锁美国出口，AI 规则默认走这里。

## 使用前必做（一次）

配置按逻辑名引用节点。先在 Shadowrocket 里把两个节点改名（改名不影响节点本身）：西雅图主力节点改名为 Seattle，Cloady 备用节点改名为 Cloady。以后换节点也只需把新节点改成同名，配置不用动。

## 导入

Shadowrocket → 配置 → 右上角 + → 粘贴地址 → 下载：
https://raw.githubusercontent.com/xiaobai111-hub/sr-rules/main/Release/Rules.conf

## 设计要点

- IPv6 关闭：防止 v6 绕过代理泄漏真实地址。
- DNS：阿里/腾讯 DoH 为主、系统 DNS 兜底，全局劫持 53 端口防泄漏。
- 仓库保持公开（Shadowrocket 拉取 raw 文件不能带登录态）；仓库里只有公开规则数据，不含任何节点信息。
