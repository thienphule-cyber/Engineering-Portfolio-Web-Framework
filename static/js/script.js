// Project filtering on the gallery page
document.addEventListener("DOMContentLoaded", () => {
    const filterButtons = document.querySelectorAll(".filter-btn");
    const projectCards = document.querySelectorAll(".project-card");

    filterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const selectedCategory = button.dataset.category;

            // Update active button state
            filterButtons.forEach((btn) => btn.classList.remove("active"));
            button.classList.add("active");

            // Show/hide project cards based on category
            projectCards.forEach((card) => {
                const cardCategory = card.dataset.category;
                if (selectedCategory === "all" || cardCategory === selectedCategory) {
                    card.style.display = "block";
                } else {
                    card.style.display = "none";
                }
            });
        });
    });
});
