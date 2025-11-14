const tg = window.Telegram.WebApp;
tg.expand();
const user = tg.initDataUnsafe?.user;

if (!user) {
    document.getElementById("history").innerHTML = "<p>Ошибка: пользователь не найден.</p>";
} else {
    fetch(`/api/history/${user.id}`)
        .then(r => r.json())
        .then(list => {
            if (!list.length) {
                document.getElementById("history").innerHTML =
                    "<p>У вас пока нет сделок.</p>";
                return;
            }

            let html = "";
            list.forEach(r => {
                html += `
                <div class="country-block">
                    <h2>ID: ${r.id}</h2>
                    <p><b>Статус:</b> ${r.status}</p>
                    <p><b>Меняете:</b> ${r.give_amount} ${r.give_currency}</p>
                    <p><b>Получите:</b> ${r.get_amount} ${r.get_currency}</p>
                    <p><b>Дата:</b> ${r.datetime}</p>
                </div>
                `;
            });

            document.getElementById("history").innerHTML = html;
        });
}