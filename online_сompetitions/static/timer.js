document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.competition-card');

    function updateTimers() {
        const now = new Date();

        cards.forEach(card => {
            const startDate = new Date(card.getAttribute('data-start-date'));
            const endDate = new Date(card.getAttribute('data-end-date'));
            const statusTimer = card.querySelector('.status-timer');
            let timeLeft, hours, minutes, seconds;

            if (now < startDate) {
                timeLeft = Math.max(0, (startDate - now) / 1000);
                hours = Math.floor(timeLeft / 3600);
                minutes = Math.floor((timeLeft % 3600) / 60);
                seconds = Math.floor(timeLeft % 60);
                statusTimer.textContent = `Идет набор конкурсантов. Осталось: ${hours}ч ${minutes}м ${seconds}с`;
            } else if (now >= startDate && now < endDate) {
                timeLeft = Math.max(0, (endDate - now) / 1000);
                hours = Math.floor(timeLeft / 3600);
                minutes = Math.floor((timeLeft % 3600) / 60);
                seconds = Math.floor(timeLeft % 60);
                statusTimer.textContent = `Идет голосование. Осталось: ${hours}ч ${minutes}м ${seconds}с`;
            } else {
                statusTimer.textContent = `Голосование завершено.`;
            }
        });
    }
    updateTimers();
    setInterval(updateTimers, 1000);
});
