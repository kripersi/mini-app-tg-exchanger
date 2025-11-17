const tg = window.Telegram?.WebApp;

document.addEventListener("DOMContentLoaded", async () => {
    const user = tg?.initDataUnsafe?.user;
    if (!user) return;

    try {
        const res = await fetch(`/api/is_admin/${user.id}`);
        const data = await res.json();

        if (data.admin) {
            const menu = document.querySelector(".menu");

            const btn = document.createElement("button");
            btn.className = "menu-item purple";
            btn.textContent = "🛠 Админ-панель";
            btn.onclick = () => location.href = `/admin?user_id=${user.id}`;

            menu.appendChild(btn);
        }
    } catch (error) {
        console.error("Ошибка проверки админа:", error);
    }
});
