const $ = (id) => document.getElementById(id);
const sourceText = $("sourceText"), targetLang = $("targetLang"), resultText = $("resultText");
const HISTORY_KEY = "doudi_translate_history_v1";
let historyItems = loadHistory();

function loadHistory(){ try{return JSON.parse(localStorage.getItem(HISTORY_KEY)||"[]")}catch{return []} }
function saveHistory(){ localStorage.setItem(HISTORY_KEY, JSON.stringify(historyItems.slice(0,30))); }
function toast(message){const el=$("toast");el.textContent=message;el.classList.add("show");setTimeout(()=>el.classList.remove("show"),2100)}
function showError(message){$("errorBox").textContent=message;$("errorBox").hidden=!message}
function updateCount(){$("charCount").textContent=`${sourceText.value.length} / 5000`}
function langName(code){const select=$(code==="source"?"sourceLang":"targetLang");if(code==="auto")return "اكتشاف تلقائي";return select.options[select.selectedIndex]?.text||code}
function renderHistory(){
  const host=$("historyList");
  if(!historyItems.length){host.innerHTML='<div class="empty-history"><span>◷</span><b>لا توجد ترجمات بعد</b><small>عندما تترجم نصاً، ستجده هنا.</small></div>';return}
  host.innerHTML="";
  historyItems.forEach((item,index)=>{
    const card=document.createElement("div");card.className="history-item";
    const left=document.createElement("div"),right=document.createElement("div");
    const a=document.createElement("span"),b=document.createElement("span"),p=document.createElement("p"),q=document.createElement("p");
    a.className=b.className="history-lang";a.textContent=item.from+" ←";b.textContent="→ "+item.to;
    p.textContent=item.original;q.textContent=item.translation;left.append(a,p);right.append(b,q);
    const btn=document.createElement("button");btn.className="history-copy";btn.textContent="نسخ الترجمة";
    btn.addEventListener("click",()=>copyText(item.translation));card.append(left,right,btn);host.append(card);
  });
}
async function copyText(value){if(!value){toast("لا توجد ترجمة لنسخها");return}try{await navigator.clipboard.writeText(value);toast("تم نسخ الترجمة")}catch{const t=document.createElement("textarea");t.value=value;document.body.append(t);t.select();document.execCommand("copy");t.remove();toast("تم النسخ")}}
async function translate(){
  const text=sourceText.value.trim();showError("");
  if(!text){showError("اكتب النص الذي تريد ترجمته أولاً.");sourceText.focus();return}
  const btn=$("translateBtn");btn.disabled=true;btn.querySelector("span").textContent="جاري الترجمة...";
  $("resultStatus").textContent="يرجى الانتظار";resultText.classList.remove("placeholder");resultText.textContent="جاري ترجمة النص...";
  try{
    const response=await fetch("/api/translate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text,source:$("sourceLang").value,target:targetLang.value})});
    const data=await response.json();if(!response.ok)throw new Error(data.error||"تعذر إتمام الترجمة.");
    resultText.textContent=data.translation;$("resultStatus").textContent="اكتملت الترجمة";$("copyBtn").disabled=false;
    historyItems.unshift({original:text,translation:data.translation,from:langName("auto"),to:langName("target"),time:Date.now()});
    historyItems=historyItems.slice(0,30);saveHistory();renderHistory();toast("تمت الترجمة بنجاح");
  }catch(error){resultText.textContent="ستظهر الترجمة هنا...";resultText.classList.add("placeholder");$("resultStatus").textContent="تعذرت الترجمة";showError(error.message)}
  finally{btn.disabled=false;btn.querySelector("span").textContent="ترجم الآن"}
}
sourceText.addEventListener("input",updateCount);
$("translateBtn").addEventListener("click",translate);
$("copyBtn").addEventListener("click",()=>copyText(resultText.textContent));
$("clearBtn").addEventListener("click",()=>{sourceText.value="";updateCount();sourceText.focus();showError("")});
$("pasteBtn").addEventListener("click",async()=>{try{sourceText.value=await navigator.clipboard.readText();updateCount();toast("تم لصق النص")}catch{toast("اسمح للموقع بالوصول إلى الحافظة")}})
$("swapBtn").addEventListener("click",()=>{
  const target=targetLang.value,source=$("sourceLang").value;
  if(source==="auto"){toast("اختر لغة المصدر أولاً حتى تتمكن من التبديل");return}
  targetLang.value=source;$("sourceLang").value=target;
  const old=sourceText.value;sourceText.value=resultText.textContent==="ستظهر الترجمة هنا..."?"":resultText.textContent;
  resultText.textContent=old||"ستظهر الترجمة هنا...";resultText.classList.toggle("placeholder",!old);$("copyBtn").disabled=!old;updateCount();
});
targetLang.addEventListener("change",()=>{const opt=targetLang.options[targetLang.selectedIndex];$("targetFlag").textContent=(opt.textContent.match(/[\u{1F1E6}-\u{1F1FF}]{2}/u)||["🌐"])[0]});
$("clearHistoryBtn").addEventListener("click",()=>{if(!historyItems.length){toast("السجل فارغ بالفعل");return}if(confirm("هل تريد مسح سجل الترجمات؟")){historyItems=[];saveHistory();renderHistory();toast("تم مسح السجل")}});
$("year").textContent=new Date().getFullYear();updateCount();renderHistory();
