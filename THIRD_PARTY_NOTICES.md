# Third-party notices

The project's MIT license covers its original Python integration, C# host, frontend glue, tools and tests. It does not replace dependency licenses.

| Component | Pinned version | License / notice |
| --- | --- | --- |
| markdown-it | 15.0.3 | MIT; `licenses/markdown-it-LICENSE.txt` |
| highlight.js CDN assets | 11.12.0 | BSD-3-Clause; `licenses/highlightjs-LICENSE.txt` |
| DOMPurify | 3.4.17 | Apache-2.0 OR MPL-2.0; complete text in `licenses/DOMPurify-LICENSE.txt` |
| Mermaid | 12.2.0 | MIT; `licenses/Mermaid-LICENSE.txt`; its distributable includes bundled dependencies |
| Microsoft WebView2 SDK | 1.0.3537.50 | Retained SDK license and notices in `licenses/WebView2-LICENSE.txt` and `licenses/WebView2-NOTICE.txt` |

The separately installed Microsoft Edge WebView2 Runtime and .NET Framework are prerequisites and are not included in the release. Their own terms apply.

The upstream Mermaid bundle also contains its own DOMPurify copy (3.4.12); updating the page's separate DOMPurify file does not update that internal copy. Upstream bundled license banners remain intact in `web/vendor/mermaid.min.js` in release archives.

`dependencies.lock.json` records the exact upstream archive URLs and integrity values. The build copies the accompanying notices without changing their terms. Dependency code is not represented as original work.
