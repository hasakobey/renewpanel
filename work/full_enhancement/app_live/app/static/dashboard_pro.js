(function(){

'use strict';


function txt(v){
    return (v || '')
        .replace(/\s+/g,' ')
        .trim()
        .toLocaleUpperCase('tr-TR');
}


function numberTR(v){

    if(v === null || v === undefined){
        return NaN;
    }

    let s = String(v)
        .replace(/\s+/g,'')
        .replace(/₺/g,'')
        .replace(/TL/gi,'')
        .replace(/%/g,'');

    if(s.includes('.') && s.includes(',')){

        s = s
            .replace(/\./g,'')
            .replace(',','.');

    }
    else if(s.includes(',')){

        s = s.replace(',','.');

    }
    else{

        const dots = (s.match(/\./g)||[]).length;

        if(dots > 1){
            s = s.replace(/\./g,'');
        }

    }

    s = s.replace(/[^0-9.\-]/g,'');

    return parseFloat(s);
}


function findColumn(headers, names){

    return headers.findIndex(h => {

        const t = txt(h.textContent);

        return names.some(n => t.includes(n));

    });

}


function sksClass(day){

    if(day >= 91) return 'rp-sks-critical';

    if(day >= 61) return 'rp-sks-high';

    if(day >= 31) return 'rp-sks-follow';

    return 'rp-sks-normal';
}


function statusFor(day){

    if(day >= 91){
        return ['Kritik','rp-status-critical'];
    }

    if(day >= 61){
        return ['Yüksek','rp-status-high'];
    }

    if(day >= 31){
        return ['Takip','rp-status-follow'];
    }

    return ['Normal','rp-status-normal'];
}


function decorateCriticalTable(){

    const box =
        document.getElementById('criticalStock');

    if(!box) return;


    const table =
        box.querySelector('table');

    if(!table) return;


    const headers =
        [...table.querySelectorAll('thead th')];


    if(!headers.length) return;


    const sksIndex =
        findColumn(
            headers,
            ['SKS']
        );


    const profitIndex =
        findColumn(
            headers,
            ['TAHMİNİ KÂR','TAHMINI KAR','KÂR','KAR']
        );


    if(sksIndex < 0) return;


    table.querySelectorAll('tbody tr')
        .forEach(row => {

            const cells =
                [...row.querySelectorAll('td')];


            const sksCell =
                cells[sksIndex];


            if(!sksCell) return;


            /*
              İlk orijinal değeri sakla.
            */

            if(!sksCell.dataset.rpOriginal){

                sksCell.dataset.rpOriginal =
                    sksCell.textContent.trim();

            }


            const days =
                numberTR(
                    sksCell.dataset.rpOriginal
                );


            if(isNaN(days)) return;


            row.classList.remove(
                'rp-critical-row',
                'rp-high-row'
            );


            if(days >= 91){

                row.classList.add(
                    'rp-critical-row'
                );

            }
            else if(days >= 61){

                row.classList.add(
                    'rp-high-row'
                );

            }


            /*
              SKS badge
            */

            sksCell.innerHTML='';

            const badge =
                document.createElement('span');

            badge.className =
                'rp-sks-badge ' +
                sksClass(days);

            badge.textContent =
                Math.round(days);

            sksCell.appendChild(badge);


            /*
              Kâr
            */

            if(profitIndex >= 0){

                const profitCell =
                    cells[profitIndex];

                if(profitCell){

                    if(
                        !profitCell.dataset.rpOriginal
                    ){

                        profitCell.dataset.rpOriginal =
                            profitCell.textContent.trim();

                    }


                    const profit =
                        numberTR(
                            profitCell.dataset.rpOriginal
                        );


                    if(!isNaN(profit)){

                        profitCell.innerHTML='';

                        const p =
                            document.createElement('span');

                        p.className='rp-profit';


                        if(profit > 0){

                            p.classList.add(
                                'rp-profit-positive'
                            );

                        }
                        else if(profit < 0){

                            p.classList.add(
                                'rp-profit-negative'
                            );

                        }
                        else{

                            p.classList.add(
                                'rp-profit-zero'
                            );

                        }


                        p.textContent =
                            profitCell.dataset.rpOriginal;

                        profitCell.appendChild(p);

                    }

                }

            }

        });


    addLegend(
        box.closest('.card') || box
    );

}


function addLegend(container){

    if(
        document.getElementById(
            'rpSksLegend'
        )
    ){
        return;
    }


    const legend =
        document.createElement('div');


    legend.id='rpSksLegend';


    legend.innerHTML=`

        <span>
            <i style="background:#148257"></i>
            0–30 Normal
        </span>

        <span>
            <i style="background:#d2a000"></i>
            31–60 Takip
        </span>

        <span>
            <i style="background:#cf6b12"></i>
            61–90 Yüksek
        </span>

        <span>
            <i style="background:#cc3737"></i>
            91+ Kritik
        </span>

    `;


    container.appendChild(legend);

}


function buildActionCenter(){

    const dashboard =
        document.getElementById('dashboard');


    const source =
        document.getElementById(
            'criticalStock'
        );


    if(!dashboard || !source) return;


    const table =
        source.querySelector('table');


    if(!table) return;


    const headers =
        [...table.querySelectorAll('thead th')];


    if(!headers.length) return;


    const plateIndex =
        findColumn(
            headers,
            ['PLAKA']
        );


    const vehicleIndex =
        findColumn(
            headers,
            ['ARAÇ','ARAC']
        );


    const sksIndex =
        findColumn(
            headers,
            ['SKS']
        );


    const profitIndex =
        findColumn(
            headers,
            ['TAHMİNİ KÂR','TAHMINI KAR','KÂR','KAR']
        );


    if(sksIndex < 0) return;


    const items=[];


    table.querySelectorAll('tbody tr')
        .forEach(row=>{

            const cells =
                [...row.querySelectorAll('td')];


            if(!cells.length) return;


            const rawDays =
                cells[sksIndex].dataset.rpOriginal
                ||
                cells[sksIndex].textContent;


            const days =
                numberTR(rawDays);


            /*
              Aksiyon merkezine sadece
              61+ gün girsin.
            */

            if(
                isNaN(days) ||
                days < 61
            ){
                return;
            }


            const plate =
                plateIndex >= 0
                ? cells[plateIndex]?.textContent.trim()
                : 'Araç';


            const vehicle =
                vehicleIndex >= 0
                ? cells[vehicleIndex]?.textContent.trim()
                : '';


            const profit =
                profitIndex >= 0
                ? (
                    cells[profitIndex]?.dataset.rpOriginal
                    ||
                    cells[profitIndex]?.textContent.trim()
                  )
                : '';


            items.push({
                plate,
                vehicle,
                days,
                profit
            });

        });


    items.sort(
        (a,b)=>b.days-a.days
    );


    let center =
        document.getElementById(
            'rpActionCenter'
        );


    if(!center){

        center =
            document.createElement('div');

        center.id='rpActionCenter';

        center.className='card';


        /*
          Kritik stok kartının hemen altına koy.
        */

        const criticalCard =
            source.closest('.card');


        if(
            criticalCard &&
            criticalCard.parentNode
        ){

            criticalCard.parentNode.insertBefore(
                center,
                criticalCard.nextSibling
            );

        }
        else{

            dashboard.appendChild(center);

        }

    }


    const top =
        items.slice(0,6);


    let body='';


    if(!top.length){

        body=`
          <div style="
            padding:16px;
            color:#6d7f92;
            font-size:11px;
          ">
            61 gün üzeri aksiyon gerektiren araç bulunmuyor.
          </div>
        `;

    }
    else{

        body=`
          <div class="rp-action-list">

            ${top.map(x=>{

                const critical =
                    x.days >= 91;


                const desc =
                    critical
                    ? 'Kritik stok süresi. Satış / fiyat aksiyonu değerlendir.'
                    : 'Kritik sınıra yaklaşıyor. Stok aksiyonunu takip et.';


                return `
                  <div class="
                    rp-action-item
                    ${critical?'critical':'high'}
                  ">

                    <div class="rp-action-icon">
                      ${critical?'🚨':'⚠️'}
                    </div>

                    <div class="rp-action-main">

                      <b>
                        ${escapeHtml(x.plate)}
                        ${x.vehicle
                          ? ' • '+escapeHtml(x.vehicle)
                          : ''
                        }
                      </b>

                      <small>
                        ${desc}
                        ${x.profit
                          ? ' • Tahmini Kâr: '+escapeHtml(x.profit)
                          : ''
                        }
                      </small>

                    </div>

                    <div class="rp-action-days">
                      ${Math.round(x.days)} Gün
                    </div>

                  </div>
                `;

            }).join('')}

          </div>
        `;

    }


    center.innerHTML=`

        <div class="rp-action-head">

            <div>
                <h3>
                    🚦 Aksiyon Gereken Araçlar
                </h3>

                <div class="rp-action-sub">
                    61 gün üzerindeki stokların yönetici özeti
                </div>
            </div>

            <button
              class="btn small"
              onclick="page('stocks')">
              Tüm Stoğu Aç
            </button>

        </div>

        ${body}

    `;

}


function escapeHtml(v){

    return String(v || '')
      .replace(/&/g,'&amp;')
      .replace(/</g,'&lt;')
      .replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;')
      .replace(/'/g,'&#039;');

}


function enhance(){

    try{

        decorateCriticalTable();

        buildActionCenter();

    }
    catch(err){

        console.warn(
            'RENEW Dashboard V2:',
            err
        );

    }

}


/*
  İlk yükleme
*/

if(
    document.readyState === 'loading'
){

    document.addEventListener(
        'DOMContentLoaded',
        enhance
    );

}
else{

    enhance();

}


/*
  Dashboard app.js ile tekrar çizildiğinde
  görünümü yeniden uygula.
*/

let t=null;

const observer =
    new MutationObserver(()=>{

        clearTimeout(t);

        t=setTimeout(
            enhance,
            180
        );

    });


document.addEventListener(
    'DOMContentLoaded',
    ()=>{

        const dash =
            document.getElementById(
                'dashboard'
            );

        if(dash){

            observer.observe(
                dash,
                {
                    childList:true,
                    subtree:true
                }
            );

        }

    }
);


/*
  Güvenli periyodik kontrol
*/

setInterval(
    enhance,
    4000
);


})();
