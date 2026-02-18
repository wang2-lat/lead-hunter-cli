# 🎯 Lead Hunter CLI

自动从 Reddit/HackerNews/ProductHunt 抓取你的目标客户并生成触达脚本。

## 🚀 快速开始

### 1. 安装依赖


### 2. 配置 API

复制 `.env.example` 为 `.env` 并填入你的 credentials：


**获取 Reddit API credentials：**
1. 访问 https://www.reddit.com/prefs/apps
2. 点击 "create another app"
3. 选择 "script" 类型
4. 复制 `client_id` 和 `client_secret` 到 `.env`

### 3. 使用


## 📊 输出格式

生成的 CSV 文件包含以下字段：
- `platform`: 来源平台 (Reddit/HackerNews/ProductHunt)
- `author`: 发帖人用户名
- `title`: 帖子标题
- `url`: 帖子链接
- `content`: 帖子内容摘要
- `score`: 帖子评分/点赞数
- `email`: 提取的邮箱（如有）
- `twitter`: Twitter 账号（如有）
- `linkedin`: LinkedIn 主页（如有）
- `email_template`: 生成的邮件模板

## 🎯 使用场景

1. **找到讨论你产品相关话题的人**
   ```bash
   python lead_hunter.py search "struggling with email marketing"
   ```

2. **发现竞品用户的抱怨**
   ```bash
   python lead_hunter.py search "Mailchimp alternatives"
   ```

3. **寻找特定行业的创始人**
   ```bash
   python lead_hunter.py search "indie maker looking for"
   ```

## ⚠️ 注意事项

1. **API 限制**：Reddit API 有速率限制，建议每次搜索不超过 100 条
2. **联系方式提取**：只能提取公开发布的联系方式，尊重隐私
3. **邮件发送**：本工具只生成模板，实际发送需要自己的邮件工具
4. **合规使用**：遵守各平台的服务条款，不要滥用

## 🔧 高级功能

### 使用 OpenAI 生成更好的邮件

在 `.env` 中添加 `OPENAI_API_KEY`，工具会自动使用 GPT 生成更个性化的邮件模板。

## 🐛 常见问题

**Q: Reddit API 返回 401 错误？**  
A: 检查 `.env` 中的 credentials 是否正确，确保应用类型是 "script"

**Q: 找不到联系方式？**  
A: 大部分用户不会公开联系方式，可以通过用户名在其他平台搜索

**Q: HackerNews 结果没有联系方式？**  
A: HN 用户很少在帖子中留联系方式，需要访问用户主页查看 about 信息

## 📝 License

MIT