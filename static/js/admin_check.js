const tg = window.Telegram?.WebApp;

document.addEventListener("DOMContentLoaded", async () => {
    const user = tg?.initDataUnsafe?.user;
    if (!user) return;

    try {
        // Запрашиваем у сервера, является ли пользователь администратором
        const res = await fetch(`/api/is_admin/${user.id}`);
        const data = await res.json();

        // Если пользователь не администратор, скрываем кнопки
        if (!data.admin) {
            document.querySelectorAll(".admin-button").forEach((btn) => {
                btn.style.display = "none";
            });
        }
    } catch (error) {
        console.error("Ошибка при проверке прав администратора:", error);
    }
});
