
    const oranlar = { 1: 0.038422, 2: 0.065303, 3: 0.087666, 4: 0.110371, 5: 0.134559, 6: 0.157943, 7: 0.180916, 8: 0.208313, 9: 0.237317, 10: 0.265022, 11: 0.299207, 12: 0.329787 };

    function musteriAlaniniAcKapat() {
        const content = document.getElementById('musteriContent');
        const icon = document.getElementById('toggleIcon');
        content.classList.toggle('show');
        icon.innerText = content.classList.contains('show') ? '-' : '+';
    }

    function bankaAlaniniAcKapat() {
        const content = document.getElementById('bankContent');
        const icon = document.getElementById('bankToggleIcon');
        content.classList.toggle('show');
        icon.innerText = content.classList.contains('show') ? '-' : '+';
    }

    function paraBicimlendir(input) {
        let deger = input.value.replace(/\D/g, '');
        if (deger !== '') deger = parseInt(deger, 10).toLocaleString('tr-TR');
        input.value = deger;
        const mailTutar = document.getElementById('mailTutar');
        if (mailTutar) { mailTutar.value = deger; mailMetniGuncelle(); }
        hesapla();
    }

    function hamTutarAl() {
        const inputVal = document.getElementById('tutar').value;
        return parseFloat(inputVal.replace(/\./g, '')) || 0;
    }

    function taksitSec(sayi) {
        document.getElementById('taksit').value = sayi;
        document.querySelectorAll('.taksit-btn').forEach(btn => {const active=parseInt(btn.innerText,10)===Number(sayi);btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',String(active));});
        hesapla();
    }

    function dropdownDegisti() {
        let val = document.getElementById('taksit').value;
        document.querySelectorAll('.taksit-btn').forEach(btn => {const active=parseInt(btn.innerText,10)===Number(val);btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',String(active));});
        hesapla();
    }

    function hesapla() {
        const tutar = hamTutarAl();
        const taksit = parseInt(document.getElementById('taksit').value);
        if (tutar <= 0) {
            ['pdfTutarOzet','toplamKomisyonTutari','aylikKomisyonTutar','aylikTaksitTutari','toplamGeriOdeme'].forEach(id=>document.getElementById(id).innerText='₺0,00');
            ['toplamKomisyonOrani','aylikKomisyonOrani'].forEach(id=>document.getElementById(id).innerText='0%');
            document.getElementById('pdfTaksitOzet').innerText=taksit+' Taksit';
            document.getElementById('sonuc').style.display = 'none';
            document.getElementById('copyBtn').style.display = 'none';
            document.getElementById('wpBtn').style.display = 'none';
            document.getElementById('pdfBtn').style.display = 'none';
            return;
        }
        const hesap = renewKartTotals(tutar,taksit);
        const komisyonOrani = hesap.rate;
        const komisyonTutari = hesap.commission;
        const toplam = hesap.total;
        
        const f = (n) => '₺' + n.toLocaleString('tr-TR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        
        document.getElementById('pdfTutarOzet').innerText = f(tutar);
        document.getElementById('pdfTaksitOzet').innerText = taksit + ' Taksit';
        document.getElementById('toplamKomisyonOrani').innerText = (komisyonOrani * 100).toFixed(2).replace('.', ',') + '%';
        document.getElementById('aylikKomisyonOrani').innerText = ((komisyonOrani/taksit) * 100).toFixed(2).replace('.', ',') + '%';
        document.getElementById('toplamKomisyonTutari').innerText = f(komisyonTutari);
        document.getElementById('aylikKomisyonTutar').innerText = f(komisyonTutari / taksit);
        document.getElementById('aylikTaksitTutari').innerText = f(toplam / taksit);
        document.getElementById('toplamGeriOdeme').innerText = f(toplam);

        document.getElementById('sonuc').style.display = 'block';
        document.getElementById('copyBtn').style.display = 'block';
        document.getElementById('wpBtn').style.display = 'flex';
        document.getElementById('pdfBtn').style.display = 'block';
    }

    function renewKartTotals(amount,term){const rate=Number(oranlar[term]||0),commission=amount*rate,total=amount+commission;return{amount,term,rate,commission,total,monthly:term?total/term:0};}
    function musteriBilgisiAl() { const isim=document.getElementById('islemYapan').value.trim(); const aciklama=document.getElementById('aracBedeliAciklama').value.trim()||"2. El Araç Bedeli"; return {isim,aciklama}; }
    function olusturMetin() {
        const {isim,aciklama}=musteriBilgisiAl();
        const isimSatiri = isim ? `*İsim Soyisim:* ${isim}\n` : '';
        const cekilenTutar = document.getElementById('pdfTutarOzet').innerText;
        const aylikTaksit = document.getElementById('aylikTaksitTutari').innerText;
        return `${isimSatiri}*Açıklama:* ${aciklama}\n\n*KREDİ KARTI ÖDEME BİLGİLERİ*\n\n*Çekilen Tutar: ${cekilenTutar}*\nTaksit Sayısı: ${document.getElementById('pdfTaksitOzet').innerText}\nToplam Komisyon Oranı: ${document.getElementById('toplamKomisyonOrani').innerText}\nAylık Komisyon Oranı: ${document.getElementById('aylikKomisyonOrani').innerText}\nToplam Komisyon Tutarı: ${document.getElementById('toplamKomisyonTutari').innerText}\nAylık Komisyon Tutarı: ${document.getElementById('aylikKomisyonTutar').innerText}\n*Aylık Taksit Tutarı: ${aylikTaksit}*\n*Toplam Geri Ödeme: ${document.getElementById('toplamGeriOdeme').innerText}*`;
    }
    function sonucuKopyala(){ const metin = olusturMetin().replace(/^\*Açıklama:\*.*\n\n/m, ""); navigator.clipboard.writeText(metin); const b=document.getElementById('copyBtn'); b.innerText="✅ Kopyalandı!"; setTimeout(()=>b.innerText="📋 Metni Kopyala",2000); }
    function whatsappGonder(){
        const url = "https://wa.me/?text=" + encodeURIComponent(olusturMetin());
        const mobil = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
        if (mobil) { window.location.href = url; } else { window.open(url, '_blank', 'noopener'); }
    }
    const bankalar=[['T.C. ZİRAAT BANKASI A.Ş.','TR97 0001 0027 9034 1200 4750 54'],['TÜRKİYE İŞ BANKASI A.Ş.','TR48 0006 4000 0016 6211 1037 73'],['TÜRKİYE VAKIFLAR BANKASI T.A.O.','TR22 0001 5001 5800 7284 2782 75'],['GARANTİ BANKASI','TR36 0006 2001 6840 0006 2025 63']];
    function bankaKopyaMetni(banka,iban){
        const {isim,aciklama}=musteriBilgisiAl();
        return `Alıcı Bilgileri: Çayan Otomotiv\n\nBanka: ${banka}\nIBAN: ${iban}\n\nÖdeme Açıklaması: ${aciklama}${isim ? ` - ${isim}` : ''}`;
    }
    function bankaMetniKopyala(banka,iban,btn){ navigator.clipboard.writeText(bankaKopyaMetni(banka,iban)); btn.innerText="✓ Kopyalandı"; setTimeout(()=>btn.innerText="Kopyala",2000); }
    function tumBankaBilgileriniKopyala(btn){
        const {isim,aciklama}=musteriBilgisiAl();
        let m=`Alıcı Bilgileri: Çayan Otomotiv\n\n🏦 BANKA HESAP BİLGİLERİ\n\n` + bankalar.map(([b,i])=>`Banka: ${b}\nIBAN: ${i}`).join('\n\n') + `\n\nÖdeme Açıklaması: ${aciklama}${isim ? ` - ${isim}` : ''}`;
        navigator.clipboard.writeText(m);
        const e=btn.innerText; btn.innerText="✅ Kopyalandı"; setTimeout(()=>btn.innerText=e,2000);
    }
    function pdfYazdir(){ document.getElementById('pdfModal').classList.add('show'); }
    function pdfSeciminiKapat(){ document.getElementById('pdfModal').classList.remove('show'); }
    function modalDisinaTikla(e){ if(e.target.id==='pdfModal') pdfSeciminiKapat(); }
    function yazdirmaBilgileriniHazirla(){
        const {isim,aciklama}=musteriBilgisiAl();
        document.getElementById('printKrediIsim').innerText='ÖRNEKTİR';
        document.getElementById('printKrediAciklama').innerText='';
        document.getElementById('printBankaIsim').innerText=isim||'-';
        document.getElementById('printBankaAciklama').innerText=aciklama;
        const x={pkTutar:'pdfTutarOzet',pkTaksit:'pdfTaksitOzet',pkToplamOran:'toplamKomisyonOrani',pkAylikOran:'aylikKomisyonOrani',pkToplamKomisyon:'toplamKomisyonTutari',pkAylikKomisyon:'aylikKomisyonTutar',pkAylikTaksit:'aylikTaksitTutari',pkToplam:'toplamGeriOdeme'};
        Object.entries(x).forEach(([a,b])=>document.getElementById(a).innerText=document.getElementById(b).innerText);
        return {isim};
    }
    function temizDosyaAdi(m){ return (m||'Musteri').replace(/[\/:*?"<>|]/g,'').replace(/\s+/g,'_'); }
    function yazdir(tur){
        const bilgi=yazdirmaBilgileriniHazirla();
        pdfSeciminiKapat();
        const kaynak = tur==='banka' ? document.getElementById('printBanka') : document.getElementById('printKredi');
        const ad = temizDosyaAdi(bilgi.isim);
        const baslik = tur==='banka' ? `Cayan_Renew_Banka_Hesaplari_${ad}` : `Cayan_Renew_Kredi_Karti_Odeme_${ad}`;

        const stil = `
            @page{size:A4;margin:11mm}
            *{box-sizing:border-box;-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}
            body{margin:0;background:#fff!important;color:#000!important;font-family:Arial,'Segoe UI',sans-serif;font-size:16px}
            .print-sheet{display:block!important;max-width:100%;margin:0 auto}
            .print-doc{color:#000!important;background:#fff!important}
            .print-header{border:0;border-radius:0;padding:20px 22px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:flex-end;background:#0b1220;color:#fff;box-shadow:inset 0 -7px 0 #f7d117}
            .print-header h1{font-size:30px;line-height:1.1;margin:7px 0 3px;font-weight:900;letter-spacing:-.4px}
            .print-header .sub{font-size:14px;font-weight:800;letter-spacing:1.5px;color:#d8dee8}
            .print-customer{background:#f3f6f9;border:2px solid #d9e0e7;border-radius:14px;padding:17px 18px;margin-bottom:18px}
            .print-customer b{font-size:19px;color:#000!important}.print-customer div{margin-top:8px;font-size:17px;line-height:1.45;color:#344054;font-weight:600}
            .print-table{width:100%;border-collapse:separate;border-spacing:0;border:2px solid #d9e0e7;border-radius:14px;overflow:hidden}
            .print-table td{padding:17px 18px;border-bottom:1px solid #bfc7d1;font-size:17px;line-height:1.25}
            .print-table tr:last-child td{border-bottom:0}
            .print-table td:first-child{color:#111!important;font-weight:800;width:56%}
            .print-table td:last-child{text-align:right;font-weight:900;font-size:18px;color:#000!important}
            .print-table tr.total td{background:#0b1220!important;color:#fff!important;font-size:22px;font-weight:900;padding:19px 17px;border:0}
            .print-bank{border:2px solid #d9e0e7;border-radius:14px;padding:18px 19px;margin-bottom:13px;page-break-inside:avoid;background:#fff}
            .print-bank-name{font-size:19px;font-weight:900;margin-bottom:10px;color:#0b1220}
            .print-bank-iban{font-family:Consolas,'Courier New',monospace;font-size:20px;line-height:1.35;font-weight:900;letter-spacing:.25px;color:#111827}
            .print-footer{margin-top:21px;border-top:2px solid #d9e0e7;padding-top:13px;font-size:14px;line-height:1.45;color:#334155!important;text-align:center;font-weight:600}
            .print-sheet,.print-sheet *{visibility:visible!important;opacity:1!important;text-shadow:none!important}
            .print-table,.print-table tr,.print-table td{background:#fff;color:#000}
            .print-table tr.total td{background:#0b1220!important;color:#fff!important}
        `;

        const pencere = window.open('', '_blank', 'width=900,height=700');
        if(!pencere){
            alert('Yazdırma penceresi tarayıcı tarafından engellendi. Lütfen bu site için açılır pencerelere izin verin.');
            return;
        }
        pencere.document.open();
        pencere.document.write(`<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${baslik}</title><style>${stil}
        /* Sağ panel: açılır/kapanır mail ve ödeme bildirimi */
        .collapsible-mail{padding:0 18px 18px!important;}
        .collapsible-mail::before{display:none!important;}
        .mail-panel-toggle{width:calc(100% + 36px);margin:0 -18px;border:0;background:#0b1220;color:#fff;padding:16px 18px;display:flex;align-items:center;justify-content:space-between;font-weight:900;font-size:.95rem;cursor:pointer;letter-spacing:.2px;}
        .mail-panel-toggle #mailPanelIcon{font-size:1.25rem;line-height:1;}
        .mail-panel-content{display:none;padding-top:14px;}
        .mail-panel-content.show{display:block;}
        .mail-section{border:1px solid #dfe5ec;border-radius:14px;overflow:hidden;background:#fff;margin-bottom:12px;}
        .mail-section-title{width:100%;border:0;background:#f6f8fb;color:#111827;padding:13px 14px;display:flex;justify-content:space-between;align-items:center;font-weight:900;cursor:pointer;text-align:left;}
        .mail-section-body{display:none;padding:14px;}
        .mail-section-body.show{display:block;}
        .short-preview{min-height:170px!important;}
        body[data-theme="light"] .mail-section{background:#fff!important;}
        body[data-theme="light"] .mail-section-title{background:#f6f8fb!important;color:#111827!important;}
        .top-actions{display:none!important;}



/* ===== V3: ORTALANMIŞ RENEW KİMLİĞİ + GELİŞMİŞ SAĞ ACCORDION ===== */
.card:before{
  content:"ÖDEME MERKEZİ"!important;
  background:#0b1220!important;
  justify-content:flex-start!important;
  padding-right:30px!important;
}
.card:after{display:none!important;}
.logo-header{
  margin:2px 0 18px!important;
  padding:0!important;
  border:0!important;
  text-align:center!important;
  display:flex!important;
  justify-content:center!important;
  align-items:center!important;
}
.renew-logo-shell{
  min-width:190px;
  min-height:68px;
  padding:12px 28px;
  border:1px solid #e2e8f0;
  border-radius:18px;
  background:#fff;
  display:flex;
  align-items:center;
  justify-content:center;
  box-shadow:0 10px 28px rgba(15,23,42,.08);
  position:relative;
}
.renew-logo-shell:after{
  content:"";
  position:absolute;
  left:34px;right:34px;bottom:-1px;
  height:4px;
  border-radius:4px 4px 0 0;
  background:var(--renew-yellow,#f7d117);
}
.renew-logo-shell img{
  display:block;
  max-width:155px!important;
  width:auto!important;
  height:40px!important;
  object-fit:contain!important;
  filter:none!important;
}
.renew-fallback{
  display:none;
  align-items:center;
  justify-content:center;
  color:#0b1220;
  font-size:32px;
  font-weight:1000;
  letter-spacing:-2px;
  text-transform:lowercase;
  line-height:1;
}

/* Sağ paneli soldaki kartlarla aynı aileye getir */
.collapsible-mail{
  padding:18px!important;
  border-radius:22px!important;
}
.mail-panel-toggle{
  width:100%!important;
  margin:0!important;
  padding:14px 15px!important;
  min-height:54px;
  border:1px solid #d9e1ea!important;
  border-radius:14px!important;
  background:#eef2f6!important;
  color:#334155!important;
  box-shadow:none!important;
  font-size:.82rem!important;
  font-weight:900!important;
  letter-spacing:.45px!important;
  text-transform:uppercase;
  transition:transform .18s ease, border-color .18s ease, background .18s ease!important;
}
.mail-panel-toggle:hover{
  background:#e7edf3!important;
  border-color:#c4ced9!important;
  transform:translateY(-1px);
}
.mail-panel-toggle .mail-plus,
.mail-section-title .mail-plus{
  flex:0 0 30px;
  width:30px;
  height:30px;
  border-radius:10px;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  background:#0b1220;
  color:#fff!important;
  font-size:18px!important;
  font-weight:800!important;
  line-height:1;
  box-shadow:0 5px 12px rgba(15,23,42,.12);
}
.mail-panel-content{
  padding-top:12px!important;
  animation:slideMailIn .24s ease both;
}
.mail-panel-content.show{display:block!important;}
@keyframes slideMailIn{
  from{opacity:0;transform:translateY(-7px)}
  to{opacity:1;transform:translateY(0)}
}
.mail-section{
  margin-bottom:10px!important;
  border:1px solid #dbe3ec!important;
  border-radius:14px!important;
  background:#fff!important;
  box-shadow:0 6px 16px rgba(15,23,42,.035)!important;
}
.mail-section-title{
  min-height:52px;
  padding:11px 12px 11px 14px!important;
  border:0!important;
  border-radius:13px!important;
  background:#f8fafc!important;
  color:#334155!important;
  font-size:.82rem!important;
  font-weight:850!important;
  letter-spacing:.15px;
}
.mail-section-title:hover{background:#f1f5f9!important;}
.mail-section-body.show{
  display:block!important;
  animation:slideSectionIn .22s ease both;
}
@keyframes slideSectionIn{
  from{opacity:0;transform:translateY(-5px)}
  to{opacity:1;transform:translateY(0)}
}
.mail-section-body{border-top:1px solid #e5eaf0;}

@media(max-width:850px){
 .renew-logo-shell{min-width:170px;min-height:62px;padding:10px 22px}
 .renew-logo-shell img{max-width:140px!important;height:36px!important}
}

</style>

<style>
/* Logosuz üst alan */
.card > .brand { margin-top: 4px !important; }

/* Mobil işlem butonları */
@media (max-width: 600px) {
    body { padding: 10px !important; }
    .card, .side-panel, .mail-panel { border-radius: 14px !important; }
    .btn-container { gap: 8px !important; }
    .action-btn { width: 100% !important; min-height: 48px; font-size: 0.95rem !important; }
    #wpBtn { min-height: 50px; border-radius: 10px !important; }
    .quick-taksit { display: grid !important; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 8px !important; }
    .result-item { gap: 12px; align-items: center; }
    .result-item span { max-width: 58%; }
    .result-item strong { text-align: right; }
}
</style>


<style>
/* ===== WEB + MOBİL YERLEŞİM DÜZELTMESİ ===== */
html,body{overflow-x:hidden!important;}
body{width:100%!important;}
.wrapper{
  width:min(1480px,calc(100vw - 44px))!important;
  margin:0 auto!important;
  grid-template-columns:310px minmax(0,1fr) 350px!important;
}
.side-panel,.mail-panel,.card{min-width:0!important;}

/* Önceki stillerden kalan absolute pseudo başlık, içerik üstüne binmesin */
.card::before{
  position:relative!important;
  left:auto!important;right:auto!important;top:auto!important;bottom:auto!important;
  width:auto!important;
  height:46px!important;
  box-sizing:border-box!important;
  margin:0 -30px 22px!important;
  padding:0 30px!important;
  flex:none!important;
  z-index:1!important;
}
.card>.brand{position:relative!important;z-index:2!important;}

@media (max-width:1240px) and (min-width:851px){
  body{padding:28px 18px 42px!important;}
  .wrapper{
    width:100%!important;
    max-width:1100px!important;
    grid-template-columns:300px minmax(0,1fr)!important;
    gap:18px!important;
  }
  .side-panel{width:100%!important;}
  .card{width:100%!important;max-width:none!important;}
  .mail-panel{grid-column:1/-1!important;width:100%!important;max-width:none!important;}
  .brand h2{font-size:1.42rem!important;}
}

@media (max-width:850px){
  body{padding:14px 10px 28px!important;}
  .wrapper{width:100%!important;max-width:620px!important;margin:0 auto!important;}
  .card::before{margin:0 -18px 18px!important;padding:0 18px!important;height:44px!important;}
  .card,.side-panel,.mail-panel{width:100%!important;max-width:none!important;}
  .brand h1{font-size:.68rem!important;}
  .brand h2{font-size:1.24rem!important;line-height:1.2!important;}
}
</style>

</head><body>${kaynak.outerHTML}<script>window.onload=function(){setTimeout(function(){window.print();},250)}<\/script></body></html>`);
        pencere.document.close();
    }
    function krediKartiPdfYazdir(){ if(hamTutarAl()<=0){alert('Kredi kartı PDF’i için önce çekilecek tutarı giriniz.');return;} yazdir('kredi'); }
    function bankaPdfYazdir(){ yazdir('banka'); }


    let seciliKartTipi = 'Tek Kredi Kartı';

    function kartTipiSec(tip) {
        seciliKartTipi = tip;
        document.getElementById('tekKartBtn').classList.toggle('active', tip === 'Tek Kredi Kartı');
        document.getElementById('cokKartBtn').classList.toggle('active', tip !== 'Tek Kredi Kartı');
        mailMetniGuncelle();
    }

    function mailTutarBicimlendir(input) {
        let deger = input.value.replace(/\D/g, '');
        if (deger !== '') deger = parseInt(deger, 10).toLocaleString('tr-TR');
        input.value = deger;
        mailMetniGuncelle();
    }

    function mailMetniOlustur() {
        const alici = document.getElementById('mailAlici').value.trim() || '[ALICI ADI SOYADI]';
        const tc = document.getElementById('mailTc').value.trim() || '[TC KİMLİK NO]';
        const cep = document.getElementById('mailCep').value.trim() || '[CEP NO]';
        const tutarHam = document.getElementById('mailTutar').value.trim() || '[TUTAR]';
        const tutar = tutarHam === '[TUTAR]' ? tutarHam : tutarHam + ' TL';

        return `Merhaba,

Aşağıda bilgileri bulunan müşterimizin kredi kartı tahsilat işlemi için desteğinizi rica ederim.

MÜŞTERİ BİLGİLERİ

Alıcı Adı Soyadı: ${alici}
T.C. Kimlik No: ${tc}
Cep Telefonu: ${cep}

ÖDEME BİLGİLERİ

Çekilecek Tutar: ${tutar}
Kredi Kartı Kullanımı: ${seciliKartTipi}

İlgili tutarın belirtilen kredi kartı/kartları üzerinden tahsilat işleminin gerçekleştirilmesini rica ederim.

İyi çalışmalar.`;
    }

    function mailMetniGuncelle() {
        const alan = document.getElementById('mailOnizleme');
        if (alan) alan.value = mailMetniOlustur();
    }

    function mailMetniniKopyala(btn) {
        const metin = mailMetniOlustur();
        navigator.clipboard.writeText(metin).then(() => {
            const eski = btn.innerText;
            btn.innerText = '✅ Mail Metni Kopyalandı';
            setTimeout(() => btn.innerText = eski, 1800);
        }).catch(() => {
            const alan = document.getElementById('mailOnizleme');
            alan.removeAttribute('readonly'); alan.select(); document.execCommand('copy'); alan.setAttribute('readonly','readonly');
            btn.innerText = '✅ Mail Metni Kopyalandı';
            setTimeout(() => btn.innerText = '📋 Mail Metnini Kopyala', 1800);
        });
    }

    const outlookAlicilar = [
        'seval.avseven@cayan.com.tr',
        'muhasebe@cayan.com.tr',
        'tahsilatsorgu@cayan.com.tr'
    ];
    const outlookBilgi = [
        'emirhan.cayan.cayan@ys.renault.com.tr',
        'denizhan.cayan.cayan@ys.renault.com.tr'
    ];
    const outlookKonu = 'Kredi Kartı Tahsilat Hk.';

    function outlookMailAc(konu, body) {
        // Outlook Web yeni ileti ekranını doğrudan açar.
        // CC/Bilgi alanını özellikle boş bırakıyoruz.
        // encodeURIComponent kullanıldığı için konu ve gövdede '+' karakteri oluşmaz.
        const to = outlookAlicilar.join(';');

        const url = 'https://outlook.office.com/mail/deeplink/compose?'
            + 'to=' + encodeURIComponent(to)
            + '&subject=' + encodeURIComponent(konu)
            + '&body=' + encodeURIComponent(body);

        window.open(url, '_blank', 'noopener,noreferrer');
    }

    function outlooktaHazirla() {
        const konu = document.getElementById('mailKonu')?.value.trim() || outlookKonu;
        outlookMailAc(konu, mailMetniOlustur());
    }

    function mailPanelAcKapat() {
        const content = document.getElementById('mailPanelContent');
        const icon = document.getElementById('mailPanelIcon');
        content.classList.toggle('show');
        icon.innerText = content.classList.contains('show') ? '−' : '+';
    }

    function mailBolumAcKapat(id, iconId) {
        const content = document.getElementById(id);
        const icon = document.getElementById(iconId);
        content.classList.toggle('show');
        icon.innerText = content.classList.contains('show') ? '−' : '+';
    }

    function odemeTutarBicimlendir(input) {
        let deger = input.value.replace(/\D/g, '');
        if (deger !== '') deger = parseInt(deger, 10).toLocaleString('tr-TR');
        input.value = deger;
        odemeMetniGuncelle();
    }

    function odemeMetniOlustur() {
        const isim = document.getElementById('odemeIsim').value.trim() || '[İSİM SOYİSİM]';
        const tutarHam = document.getElementById('odemeTutar').value.trim() || '[TUTAR]';
        const tutar = tutarHam === '[TUTAR]' ? tutarHam : tutarHam + ' TL';
        const banka = document.getElementById('odemeBanka').value || '[BANKA]';
        return `Merhaba,

${isim} isimli müşterimiz tarafından ${banka} hesabımıza ${tutar} tutarında ödeme gönderimi sağlanmıştır.

Kontrolünü sağlayabilir miyiz?

İyi çalışmalar.`;
    }

    function odemeMetniGuncelle() {
        const alan = document.getElementById('odemeOnizleme');
        if (alan) alan.value = odemeMetniOlustur();
    }

    function odemeMetniniKopyala(btn) {
        const metin = odemeMetniOlustur();
        navigator.clipboard.writeText(metin).then(() => {
            const eski = btn.innerText;
            btn.innerText = '✅ Ödeme Bildirimi Kopyalandı';
            setTimeout(() => btn.innerText = eski, 1800);
        }).catch(() => {
            const alan = document.getElementById('odemeOnizleme');
            alan.removeAttribute('readonly'); alan.select(); document.execCommand('copy'); alan.setAttribute('readonly','readonly');
            btn.innerText = '✅ Ödeme Bildirimi Kopyalandı';
            setTimeout(() => btn.innerText = '📋 Ödeme Bildirimini Kopyala', 1800);
        });
    }

    function odemeKonuOlustur() {
        const isim = document.getElementById('odemeIsim').value.trim() || 'İsim Soyisim';
        const tutarHam = document.getElementById('odemeTutar').value.trim() || 'Tutar';
        const tutar = tutarHam === 'Tutar' ? tutarHam : tutarHam + ' TL';
        const bankaSecim = document.getElementById('odemeBanka');
        const banka = bankaSecim.options[bankaSecim.selectedIndex]?.text || 'Banka';
        return `${isim} - ${tutar} - ${banka}`;
    }

    function odemeOutlooktaHazirla() {
        outlookMailAc(odemeKonuOlustur(), odemeMetniOlustur());
    }



    let sigortaIslemTipi = 'iptal';

    function sigortaIslemSec(tip) {
        sigortaIslemTipi = tip === 'yap' ? 'yap' : 'iptal';
        document.getElementById('sigortaIptalBtn')?.classList.toggle('active', sigortaIslemTipi === 'iptal');
        document.getElementById('sigortaYapBtn')?.classList.toggle('active', sigortaIslemTipi === 'yap');
        const label = document.getElementById('sigortaHazirLabel');
        if (label) label.innerText = sigortaIslemTipi === 'iptal' ? 'Hazır Sigorta İptali Metni' : 'Hazır Sigorta İşlemi Metni';
        const copy = document.getElementById('sigortaCopyBtn');
        if (copy) copy.innerText = sigortaIslemTipi === 'iptal' ? '📋 Sigorta İptali Metnini Kopyala' : '📋 Sigorta İşlemi Metnini Kopyala';
        sigortaMetniGuncelle();
    }

    function sigortaPlakaBicimlendir(input) {
        input.value = input.value.toLocaleUpperCase('tr-TR').replace(/[^0-9A-ZÇĞİÖŞÜ ]/g, '').replace(/\s+/g, ' ').trimStart();
    }

    function sigortaKonuOlustur() {
        const plaka = document.getElementById('sigortaPlaka').value.trim() || 'PLAKA';
        return sigortaIslemTipi === 'iptal' ? `${plaka} Sigorta İptali Hk.` : `${plaka} Sigorta İşlemi Hk.`;
    }

    function sigortaMetniOlustur() {
        const plaka = document.getElementById('sigortaPlaka').value.trim() || '[PLAKA]';
        if (sigortaIslemTipi === 'iptal') {
            return `Merhaba,

${plaka} plakalı aracın sigorta iptal işlemini gerçekleştirebilir misiniz?

İyi çalışmalar,
Saygılarımla.`;
        }
        return `Merhaba,

${plaka} plakalı araç için sigorta poliçesi düzenlenmesini rica ederim.

İyi çalışmalar,
Saygılarımla.`;
    }

    function sigortaMetniGuncelle() {
        const alan = document.getElementById('sigortaOnizleme');
        if (alan) alan.value = sigortaMetniOlustur();
        const konu = document.getElementById('sigortaKonuNotu');
        if (konu) konu.innerText = 'Konu: ' + sigortaKonuOlustur();
    }

    function sigortaMetniniKopyala(btn) {
        const metin = sigortaMetniOlustur();
        navigator.clipboard.writeText(metin).then(() => {
            const eski = btn.innerText;
            btn.innerText = sigortaIslemTipi === 'iptal' ? '✅ Sigorta İptali Metni Kopyalandı' : '✅ Sigorta İşlemi Metni Kopyalandı';
            setTimeout(() => btn.innerText = eski, 1800);
        }).catch(() => {
            const alan = document.getElementById('sigortaOnizleme');
            alan.removeAttribute('readonly'); alan.select(); document.execCommand('copy'); alan.setAttribute('readonly','readonly');
        });
    }

    function sigortaOutlooktaHazirla() {
        const sigortaAlicilar = [
            'muhasebe@cayan.com.tr',
            'Sezen.Tanrisever@kocstellantissigorta.com.tr'
        ];
        const url = 'https://outlook.office.com/mail/deeplink/compose?'
            + 'to=' + encodeURIComponent(sigortaAlicilar.join(';'))
            + '&subject=' + encodeURIComponent(sigortaKonuOlustur())
            + '&body=' + encodeURIComponent(sigortaMetniOlustur());
        window.open(url, '_blank', 'noopener,noreferrer');
    }

    document.addEventListener('DOMContentLoaded', () => {
        mailMetniGuncelle();
        odemeMetniGuncelle();
        sigortaIslemSec('iptal');
    });


    /* ===== DEVİR İŞLEMİ MAİLİ ===== */
    let devirPlakaDurumu = 'ayni';
    let devirKonuTipi = 'devir';

    function devirKonuSec(tip){
        devirKonuTipi = tip === 'alis' ? 'alis' : 'devir';
        document.getElementById('devirAlisKonuBtn')?.classList.toggle('active', devirKonuTipi === 'alis');
        document.getElementById('devirDevirKonuBtn')?.classList.toggle('active', devirKonuTipi === 'devir');
        const note=document.getElementById('devirKonuNotu');
        if(note) note.innerText='Alıcı: g.n.d@hotmail.com • Bilgi (CC) boş • Konu: '+devirKonuOlustur();
    }
    function devirKonuOlustur(){ return devirKonuTipi === 'alis' ? 'Çayan Alış Hk.' : 'Çayan Devir Hk.'; }
    function devirTutarBicimlendir(input){ let d=input.value.replace(/\D/g,''); if(d!=='') d=parseInt(d,10).toLocaleString('tr-TR'); input.value=d; devirMetniGuncelle(); }
    function devirKmBicimlendir(input){ let d=input.value.replace(/\D/g,''); if(d!=='') d=parseInt(d,10).toLocaleString('tr-TR'); input.value=d; devirMetniGuncelle(); }
    function devirPlakaSec(durum){ devirPlakaDurumu=durum; document.getElementById('plakaAyniBtn').classList.toggle('active',durum==='ayni'); document.getElementById('plakaDegisecekBtn').classList.toggle('active',durum==='degisecek'); devirMetniGuncelle(); }
    function devirMetniOlustur(){ const t=document.getElementById('devirTutar').value.trim(); const k=document.getElementById('devirKm').value.trim(); const y=document.getElementById('devirYetkili').value; const tutar=t?t+' TL':'[ARAÇ BEDELİ]'; const km=k?k+' KM':'[KM]'; const p=devirPlakaDurumu==='degisecek'?'Plaka değişecektir.':'Plaka aynı kalacaktır.'; return `Merhaba, Çayan Otomotiv adına ${y} imza yetkilisidir. Araç bedeli ${tutar}'dir. Araç ${km}'dedir. ${p} İyi çalışmalar.`; }
    function devirMetniGuncelle(){ const a=document.getElementById('devirOnizleme'); if(a) a.value=devirMetniOlustur(); }
    function devirMetniniKopyala(btn){ const m=devirMetniOlustur(); navigator.clipboard.writeText(m).then(()=>{const e=btn.innerText;btn.innerText='✅ Devir Maili Kopyalandı';setTimeout(()=>btn.innerText=e,1800)}).catch(()=>{const a=document.getElementById('devirOnizleme');a.removeAttribute('readonly');a.select();document.execCommand('copy');a.setAttribute('readonly','readonly');}); }
    function devirOutlooktaHazirla(){ const url='https://outlook.office.com/mail/deeplink/compose?to='+encodeURIComponent('g.n.d@hotmail.com')+'&subject='+encodeURIComponent(devirKonuOlustur())+'&body='+encodeURIComponent(devirMetniOlustur()); window.open(url,'_blank','noopener,noreferrer'); }

    /* ===== NAKİT / TAKAS BEDELİ ÖDEME TALEBİ ===== */
    function nakitPlakaBicimlendir(input){ input.value=input.value.toLocaleUpperCase('tr-TR').replace(/[^0-9A-ZÇĞİÖŞÜ ]/g,'').replace(/\s+/g,' ').trimStart(); nakitMetniGuncelle(); }
    function nakitIbanBicimlendir(input){ input.value=input.value.toUpperCase().replace(/[^A-Z0-9 ]/g,'').replace(/\s+/g,' ').trimStart(); nakitMetniGuncelle(); }
    function nakitTutarBicimlendir(input){ let d=input.value.replace(/\D/g,''); if(d!=='') d=parseInt(d,10).toLocaleString('tr-TR'); input.value=d; nakitMetniGuncelle(); }
    function nakitKonuOlustur(){ const plaka=document.getElementById('nakitPlaka').value.trim()||'PLAKA'; return `${plaka} Plakalı Araç – Takas Bedeli Ödeme Talebi`; }
    function nakitMetniOlustur(){
        const plaka=document.getElementById('nakitPlaka').value.trim()||'[PLAKA]';
        const aracSahibi=document.getElementById('nakitAracSahibi').value.trim()||'[ARAÇ SAHİBİ / RUHSAT SAHİBİ]';
        const hesapSahibi=document.getElementById('nakitHesapSahibi').value.trim()||'[HESAP SAHİBİ]';
        const banka=document.getElementById('nakitBanka').value.trim()||'[BANKA]';
        const iban=document.getElementById('nakitIban').value.trim()||'[IBAN]';
        const th=document.getElementById('nakitTutar').value.trim()||'[TUTAR]';
        const tutar=th==='[TUTAR]'?th:th+' TL';
        const aciklama=document.getElementById('nakitAciklama').value.trim()||`${plaka} Plakalı Araç Bedeli`;
        return `Merhaba,

${plaka} plakalı, ${aracSahibi} adına kayıtlı araç, ${tutar} bedel ile Çayan Otomotiv adına takasa alınmıştır.

İlgili araç bedelinin aşağıda belirtilen banka hesabına ödenmesini rica ederim.

ÖDEME BİLGİLERİ
Hesap Sahibi: ${hesapSahibi}
Banka: ${banka}
IBAN: ${iban}
Ödenecek Tutar: ${tutar}
Açıklama: ${aciklama}

Ödemenin gerçekleştirilmesi hususunda gereğini rica eder, iyi çalışmalar dilerim.

Saygılarımla,
Onur İpek
Çayan Otomotiv`;
    }
    function nakitMetniGuncelle(){ const a=document.getElementById('nakitOnizleme'); if(a) a.value=nakitMetniOlustur(); const n=document.getElementById('nakitKonuNotu'); if(n) n.innerText='Konu: '+nakitKonuOlustur(); }
    function nakitMetniniKopyala(btn){ const m=nakitMetniOlustur(); navigator.clipboard.writeText(m).then(()=>{const e=btn.innerText;btn.innerText='✅ Nakit Ödeme Talebi Kopyalandı';setTimeout(()=>btn.innerText=e,1800)}).catch(()=>{const a=document.getElementById('nakitOnizleme');a.removeAttribute('readonly');a.select();document.execCommand('copy');a.setAttribute('readonly','readonly');}); }
    function nakitOutlooktaHazirla(){ outlookMailAc(nakitKonuOlustur(),nakitMetniOlustur()); }

    document.addEventListener('DOMContentLoaded',()=>{
        devirMetniGuncelle();
        devirKonuSec('devir');
        nakitMetniGuncelle();
    });
