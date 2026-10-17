const parser=window.markdownit({html:true,linkify:true,typographer:false,highlight(code,lang){
  if(lang==='mermaid')return '<pre class="mermaid">'+parser.utils.escapeHtml(code)+'</pre>';
  if(lang&&hljs.getLanguage(lang))return '<pre><code class="hljs language-'+parser.utils.escapeHtml(lang)+'">'+hljs.highlight(code,{language:lang}).value+'</code></pre>';
  return '<pre><code>'+parser.utils.escapeHtml(code)+'</code></pre>';
}});
mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'default'});
let currentText='', renderId=0;
window.updatePreview=function(payload){
  if(payload.markdown===currentText&&document.querySelector('base')?.href===payload.baseUri)return {unchanged:true};
  const previous=window.scrollY;
  const selection=window.getSelection();
  const selected=selection?selection.toString():'';
  let base=document.querySelector('base');if(!base){base=document.createElement('base');document.head.prepend(base)}base.href=payload.baseUri;
  currentText=payload.markdown;
  const html=DOMPurify.sanitize(parser.render(payload.markdown),{FORBID_TAGS:['script','iframe','object','embed','form'],ADD_ATTR:['class']});
  document.getElementById('content').innerHTML=html;
  document.querySelectorAll('li').forEach(li=>{const first=li.firstChild;if(first&&first.nodeType===3&&/^\[[ xX]\] /.test(first.textContent)){const checked=/^\[[xX]\]/.test(first.textContent);const box=document.createElement('input');box.type='checkbox';box.disabled=true;box.checked=checked;first.textContent=first.textContent.slice(4);li.prepend(box)}});
  document.querySelectorAll('a').forEach(a=>{a.rel='noopener noreferrer';a.target='_blank'});
  const id=++renderId;
  const diagrams=Array.from(document.querySelectorAll('.mermaid'));
  if(diagrams.length)mermaid.run({nodes:diagrams}).catch(error=>{if(id===renderId)console.warn(error)});
  window.scrollTo(0,previous);
  document.documentElement.dataset.rendered='true';
  return {renderId:id,headings:document.querySelectorAll('h1,h2,h3').length,tables:document.querySelectorAll('table').length,images:document.images.length,selectionBefore:selected};
};
