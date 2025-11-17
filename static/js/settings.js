const tg = window.Telegram?.WebApp;
if (tg) tg.expand();

document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("saveProfileBtn");
    const form = document.getElementById("updateProfileForm");

    btn.addEventListener("click", async () => {
        const formData = new FormData(form);

        try {
            const res = await fetch("/api/update_profile", {
                method: "POST",
                body: formData
            });

            const data = await res.json();

            if (data.success) {
                tg?.showAlert("Данные успешно сохранены!");
                window.location.href = "/";
            } else {
                showNotification(data.error || "Ошибка сохранения");
            }
        } catch (err) {
            console.error(err);
            showNotification("Ошибка соединения");
        }
    });

    function showNotification(msg) {
        const box = document.getElementById("notification-container");
        const div = document.createElement("div");
        div.className = "notification";
        div.innerText = msg;
        box.appendChild(div);
        setTimeout(() => div.remove(), 3000);
    }
});
