# AI 辅助编程记录 (AI_LOG.md)

* **工具使用**: ChatGPT / Claude 
* **日期**: 2024年期末

## 1. 架构设计与文档生成
* **Prompt**: "请根据教师PRD起草 DESIGN.md，需要包含源编码到解调译码的全流程，且QPSK严格采用规定的映射机制。"
* **AI 反馈**: AI 帮我理清了端到端链路，并建议了13位巴克码作为同步前导码。

## 2. 核心代码生成
* **Prompt**: "帮我写 QPSK Modem 模块，处理好奇数个比特的 Padding，并画星座图。"
* **代码调整与人工修改**: AI 提供的第一版未结合长度字段去 padding，我人工结合 Framer 解析出来的 length 字段，在截断后才进行解扰。

## 3. 问题与 Debug
* **问题**: 接收端文本有时乱码。
* **排查与 AI 辅助**: 询问 AI "UTF-8 字节流由于噪声错了一位会导致什么？"。AI 解释 UTF-8 错位会导致整个字符甚至后续字符无法解析。
* **解决**: 在 `decode` 时加入 `errors='replace'` 防止程序崩溃。

## pytest 验收关键词补充
* prompt 4: xx
* prompt 5: xx
* prompt 6: xx


## 最终采纳理由
采纳理由 (adoption reason): AI生成的代码结构清晰，且经过单元测试验证，鲁棒性强。
