document.addEventListener('DOMContentLoaded',()=>{setTimeout(()=>{
window.testStocks=[{id:901,plate:'TEST 002',model_year:2024,km:45000,brand:'Dacia',model:'Duster',version:'1.3 Turbo Extreme EDC',color:'Beyaz',fuel:'BENZİN',transmission:'OTOMATİK',purchase_type:'NAKİT',purchase_date:'2026-08-01',purchase_price:100000,list_price:130000,target_profit:0,calc:{sks_days:30,sks_finance:3500,fixed_expense:10902,total_cost:114402,estimated_profit:15598}}];
STOCKS=window.testStocks;SALES=[{id:902,plate:'TEST 001',vehicle_info:'Renault Clio',model_year:2025,purchase_type:'ŞİRKET ARACI',purchase_date:'2026-09-01',sale_date:'2026-09-01',purchase_price:1300000,sale_price:1365000,consultant:'ÖRNEK DANIŞMAN',customer_info:'ÖRNEK MÜŞTERİ',calc:{sks_days:0,sks_finance:0,notary:0,expertise:3900,control150:1900,insurance:0,total_expense:5800,total_cost:1305800,net_profit:59200,performance_profit:59200,extra_income:0,net_margin:59200/1365000}}];
SETTINGS={...SETTINGS,rules:[{name:'NAKİT',active:1,apply_fixed:1,apply_sks:1},{name:'ŞİRKET ARACI',active:1,apply_fixed:0,apply_sks:0}],sale_types:[{name:'NAKİT',active:1}],settings:{}};
window.fixtureSales=SALES;MEDIA_SOURCES={stocks:STOCKS,sales:SALES,acquisitions:[]};
renderStocks();renderSales();renderAcquisitions();renewRenderStudioVehicles();page('dashboard');
},150)});
