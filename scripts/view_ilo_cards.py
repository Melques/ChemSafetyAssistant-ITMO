"""Build a standalone, offline HTML viewer of the existing ILO CSV."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/substances.csv"
OUTPUT = ROOT / "data/processed/ilo_cards.html"

TEMPLATE = r'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ILO · Каталог химических веществ</title>
<style>
:root{font-family:Segoe UI,Arial,sans-serif;color:#193138;background:#f2f6f5;color-scheme:light}
*{box-sizing:border-box}body{margin:0}button,input,select{font:inherit}button,select{cursor:pointer}
header{padding:30px 36px 23px;background:#123e42;color:white}header small{letter-spacing:3px;color:#8fe0ca;font-weight:700}
h1{margin:8px 0;font-size:30px;font-weight:600}header p{margin:0;color:#c6dada;font-size:14px}
main{padding:22px 30px}.toolbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
input{flex:1;min-width:260px}input,select,button,.download{padding:11px 14px;border:1px solid #cbdad6;border-radius:8px;background:white;color:#193138}
input:focus,button:focus-visible,select:focus{outline:3px solid #72cdb9;outline-offset:1px}.download{text-decoration:none;font-size:14px}
.meta{display:flex;justify-content:space-between;gap:16px;align-items:center;margin:12px 0;font-size:13px;color:#59716d}
.badge{display:inline-block;background:#def2ea;color:#216854;border-radius:5px;padding:3px 7px;font-size:12px}
.sheet{overflow:auto;max-height:calc(100vh - 310px);min-height:240px;border:1px solid #d7e2de;border-radius:10px;background:white}
table{border-collapse:separate;border-spacing:0;width:100%;font-size:13px}th{position:sticky;top:0;z-index:2;background:#e7efec;text-align:left;white-space:normal;min-width:180px;padding:0;border-bottom:1px solid #bfcec8}
th button{border:0;border-radius:0;background:none;width:100%;text-align:left;font-size:12px;font-weight:650;padding:14px;overflow-wrap:anywhere}
td{border-bottom:1px solid #e7eeeb;padding:13px 14px;vertical-align:top;min-width:180px;max-width:350px}
th:first-child,td:first-child{position:sticky;left:0;min-width:250px;max-width:300px;border-right:1px solid #d7e2de;background:#fff;z-index:1}th:first-child{background:#e7efec;z-index:3}
tr:nth-child(even) td{background:#f7faf9}tr:hover td{background:#edf7f3}.cell{white-space:pre-wrap;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;line-height:1.5}
.name{padding:0;background:none;border:0;text-align:left;font-size:13px;font-weight:650;color:#176e64;line-height:1.5}.empty{color:#9baaa5}
footer{display:flex;justify-content:space-between;align-items:center;padding:14px 0;font-size:13px;gap:12px}footer button{padding:8px 14px}button:disabled{opacity:.4;cursor:default}
dialog{border:0;border-radius:14px;width:min(1050px,94vw);max-height:90vh;padding:0;box-shadow:0 25px 90px #102e4260}dialog::backdrop{background:#102c3c88}
.dialog-head{position:sticky;top:0;background:#fff;padding:22px 26px;border-bottom:1px solid #dce7e2;display:flex;justify-content:space-between;align-items:center;gap:15px}h2{margin:0 0 6px;font-size:22px}.details{padding:8px 26px 26px}dl{margin:0}.field{display:grid;grid-template-columns:280px 1fr;gap:20px;padding:15px 0;border-bottom:1px solid #e7eeeb}dt{font-size:12px;color:#59716d;overflow-wrap:anywhere}dd{margin:0;white-space:pre-wrap;font-size:14px;line-height:1.65}
@media(max-width:700px){header{padding:22px}main{padding:15px}.field{grid-template-columns:1fr;gap:6px}.meta{flex-wrap:wrap}h1{font-size:24px}}
</style></head><body>
<header><small>CHEMSAFETY / ILO · ICSC</small><h1>Каталог химических веществ</h1>
<p id="subtitle"></p></header>
<main><div class="toolbar"><input id="search" type="search" aria-label="Поиск по всем полям" placeholder="Поиск по названию, CAS, ICSC или любому тексту…">
<select id="group" aria-label="Набор колонок"><option value="overview">Обзор</option><option value="all">Все 50 колонок</option><option value="safety">Опасности и защита</option><option value="properties">Физические свойства</option><option value="health">Воздействие на организм</option></select>
<a class="download" href="substances.csv" download>Скачать CSV ↓</a></div>
<div class="meta"><span id="count" aria-live="polite"></span><span>Нажмите на название — полная карточка · На заголовок — сортировка</span></div>
<div class="sheet"><table><thead id="head"></thead><tbody id="body"></tbody></table></div>
<footer><span>Пустые значения: — · Текст и единицы сохранены из CSV</span><div><button id="prev" aria-label="Предыдущая страница">←</button> <span id="page"></span> <button id="next" aria-label="Следующая страница">→</button></div></footer></main>
<dialog id="detail"><div class="dialog-head"><div><h2 id="detail-name"></h2><span id="detail-id" class="badge"></span></div><button id="close">Закрыть ✕</button></div><div class="details"><dl id="fields"></dl></div></dialog>
<script id="dataset" type="application/json">__DATA__</script>
<script>
const data=JSON.parse(document.getElementById('dataset').textContent),cols=data.columns,rows=data.rows;
const $=id=>document.getElementById(id),size=40;
let page=0,sortKey='',direction=1,filtered=rows.slice();
const groups={overview:['name','icsc_number','cas','un_number','specific_hazards','storage','classification_and_labelling','lang'],all:cols,safety:[cols[0],...cols.slice(5,26)],properties:[cols[0],...cols.slice(27,40)],health:[cols[0],...cols.slice(8,20),...cols.slice(40,48)]};
const searchable=rows.map(r=>cols.map(c=>r[c]).join('\n').toLocaleLowerCase());
$('subtitle').textContent=`${rows.length.toLocaleString('ru-RU')} карточка · ${cols.length} полей · Источник: substances.csv · Языки: ${[...new Set(rows.map(r=>r.lang))].join(', ')}`;
function element(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e}
function show(row){$('detail-name').textContent=row.name;$('detail-id').textContent=`ICSC ${row.icsc_number} · CAS ${row.cas||'—'} · ${row.lang}`;$('fields').replaceChildren();for(const col of cols){const item=element('div',undefined,'field');item.append(element('dt',col),element('dd',row[col]||'—',row[col]?'':'empty'));$('fields').append(item)}$('detail').showModal();$('detail').scrollTop=0}
function render(){const selected=groups[$('group').value],pages=Math.max(1,Math.ceil(filtered.length/size));page=Math.min(page,pages-1);const hr=element('tr');for(const col of selected){const th=element('th');th.scope='col';const b=element('button',col+(sortKey===col?(direction===1?' ↑':' ↓'):''));b.onclick=()=>{direction=sortKey===col?-direction:1;sortKey=col;filtered.sort((a,b)=>a[col].localeCompare(b[col],'ru',{numeric:true})*direction);page=0;render()};th.append(b);hr.append(th)}$('head').replaceChildren(hr);const fragment=document.createDocumentFragment();for(const row of filtered.slice(page*size,(page+1)*size)){const tr=element('tr');for(const col of selected){const td=element('td');if(col==='name'){const b=element('button',row[col],'name');b.onclick=()=>show(row);td.append(b)}else{td.append(element('div',row[col]||'—',row[col]?'cell':'cell empty'));td.title=row[col]}tr.append(td)}fragment.append(tr)}if(!filtered.length){const td=element('td','Ничего не найдено. Попробуйте другой запрос.');td.colSpan=selected.length;const tr=element('tr');tr.append(td);fragment.append(tr)}$('body').replaceChildren(fragment);$('count').textContent=`Найдено: ${filtered.length.toLocaleString('ru-RU')} из ${rows.length.toLocaleString('ru-RU')} · Колонок: ${selected.length}`;$('page').textContent=`${page+1} / ${pages}`;$('prev').disabled=page===0;$('next').disabled=page>=pages-1}
let timer;$('search').oninput=()=>{clearTimeout(timer);timer=setTimeout(()=>{const q=$('search').value.trim().toLocaleLowerCase();filtered=rows.filter((r,i)=>searchable[i].includes(q));if(sortKey)filtered.sort((a,b)=>a[sortKey].localeCompare(b[sortKey],'ru',{numeric:true})*direction);page=0;render()},160)};
$('group').onchange=render;$('prev').onclick=()=>{page--;render()};$('next').onclick=()=>{page++;render()};$('close').onclick=()=>$('detail').close();render();
</script></body></html>'''


def main():
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        data = {"columns": reader.fieldnames, "rows": list(reader)}
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    OUTPUT.write_text(TEMPLATE.replace("__DATA__", payload), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
