# Markdown 完整渲染测试

这是 **真正的粗体**、*斜体*、~~删除线~~，以及 `行内代码`。

## 表格

| 功能 | 实现方式 | 状态 |
| --- | --- | --- |
| 原窗口预览 | WebView2 子窗口 | 实际验证 |
| 图片与表格 | HTML 渲染 | 实际验证 |
| 文字选择复制 | 浏览器原生选择 | 实际验证 |

## 图片

![本地图片测试](sample.svg)

## 代码高亮

```javascript
function preview(markdown) {
  const message = "真正的 HTML 预览";
  return markdown.render(message);
}
```

## 流程图

```mermaid
graph LR
  A[编辑 Markdown] --> B[原窗口实时预览]
  B --> C[选中并复制文字]
```

## 任务列表

- [x] 保留源文档和原窗口
- [ ] 用户实际体验确认

> 左侧编辑，右侧自动更新。无需保存即可预览。
