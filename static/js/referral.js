// tg: Marpexiz
const tg = window.Telegram.WebApp;
tg.expand();

const user = tg.initDataUnsafe?.user;

async function loadReferralData() {
    // 1. Получаем основную инфу
    const base = await fetch(`/api/referral/${user.id}`).then(r => r.json());

    // 2. Получаем ссылку через Telegram Bot API
    const linkData = await fetch(`/api/referral_link/${user.id}`).then(r => r.json());

    base.link = linkData.link;

    document.getElementById("ref-info").innerHTML = `
        <p><b>Ваша ссылка:</b><br>
            <input id="refLink" class="ref-input" value="${base.link}" readonly>
            <button onclick="copyLink()" class="copy-btn">📋 Копировать</button>
        </p>
        <p><b>Приглашено:</b> ${base.count}</p>
    `;

    let html = "";
    base.list.forEach(p => {
        html += `
            <div class="referral-block">
                <p><b>ID:</b> ${p.invited_id}</p>
                <p><b>Username:</b> ${p.username ? '@' + p.username : '—'}</p>
            </div>`;
    });


    document.getElementById("ref-list").innerHTML = html || "<p>Пока нет приглашённых.</p>";
}

function copyLink() {
    const input = document.getElementById("refLink");
    input.select();
    input.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(input.value);
}

loadReferralData();
