(function(){
  var checks=Array.from(document.querySelectorAll("[data-check-row]"));
  var fill=document.querySelector("[data-progress-fill]");
  var label=document.querySelector("[data-progress-label]");
  var key="wisp-onboarding-v1",state={};
  try{state=JSON.parse(localStorage.getItem(key)||"{}")}catch(_){state={}}
  function render(){var done=0;checks.forEach(function(row){var k=row.dataset.checkRow,b=row.querySelector("[data-check-toggle]"),yes=Boolean(state[k]);row.classList.toggle("done",yes);b.setAttribute("aria-pressed",String(yes));b.textContent=yes?(b.dataset.done||"Ready"):(b.dataset.todo||"Mark ready");if(yes)done++});if(fill)fill.style.width=(checks.length?Math.round(done/checks.length*100):0)+"%";if(label)label.textContent=done+" / "+checks.length;try{localStorage.setItem(key,JSON.stringify(state))}catch(_){}}
  checks.forEach(function(row){var b=row.querySelector("[data-check-toggle]");if(b)b.addEventListener("click",function(){state[row.dataset.checkRow]=!state[row.dataset.checkRow];render()})});
  function fallback(text){var e=document.createElement("textarea");e.value=text;e.setAttribute("readonly","");e.style.position="fixed";e.style.opacity="0";document.body.appendChild(e);e.select();document.execCommand("copy");e.remove()}
  document.querySelectorAll("[data-copy]").forEach(function(b){b.addEventListener("click",function(){var text=b.dataset.copy||"",old=b.dataset.label||b.textContent,ok=function(){b.textContent=b.dataset.copied||"Copied";setTimeout(function(){b.textContent=old},1400)};if(navigator.clipboard&&window.isSecureContext)navigator.clipboard.writeText(text).then(ok).catch(function(){fallback(text);ok()});else{fallback(text);ok()}})});
  render();
})();
