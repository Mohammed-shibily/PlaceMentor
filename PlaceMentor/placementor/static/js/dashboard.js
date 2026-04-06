document.addEventListener('DOMContentLoaded', () => {

    // 1. Custom Cursor removed per preference (using native cursors now for zero latency and better UX)

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // 2. Initial Page Load Animations
    if (!prefersReducedMotion) {
        // Navbar slides down handled by CSS sticky + animation naturally on page load usually
        // Profile Card
        const heroCard = document.querySelector('.hero-card');
        if (heroCard) {
            heroCard.style.opacity = 0;
            heroCard.style.transform = 'translateY(20px)';
            setTimeout(() => {
                heroCard.style.transition = 'all 0.6s ease';
                heroCard.style.opacity = 1;
                heroCard.style.transform = 'translateY(0)';
            }, 200);
        }

        // Stats Cards Stagger
        const statsCards = document.querySelectorAll('.stat-card');
        statsCards.forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = 1;
                card.style.transform = 'translateY(0)';
            }, 400 + (index * 100)); // 400, 500, 600, 700
        });

        // Skill Tags Stagger
        const skillTags = document.querySelectorAll('.skill-tag-modern');
        skillTags.forEach((tag, index) => {
            setTimeout(() => {
                // remove slide logic here to let scroll reveal handle it or do it on load
                // wait, if they are top of page, animate now
                tag.style.opacity = 1;
                tag.style.transform = 'translateX(0)';
            }, 800 + (index * 80));
        });
    } else {
        // Fallback for reduced motion
        document.querySelectorAll('.stat-card, .hero-card, .skill-tag-modern, .reveal-on-scroll').forEach(el => {
            el.style.opacity = 1;
            el.style.transform = 'none';
        });
    }

    // 3. Stat Counter (CountUp) On Scroll / Ready
    const statCounters = document.querySelectorAll('.stat-value');
    
    const countUpObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !prefersReducedMotion) {
                const targetEl = entry.target;
                const finalValue = parseFloat(targetEl.getAttribute('data-value'));
                const isFloat = finalValue % 1 !== 0 || targetEl.getAttribute('data-is-float') === 'true';
                
                let startTimestamp = null;
                const duration = 1500; // 1.5s
                
                const step = (timestamp) => {
                    if (!startTimestamp) startTimestamp = timestamp;
                    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                    
                    // easeOutQuart
                    const easeProgress = 1 - Math.pow(1 - progress, 4);
                    const currentVal = (easeProgress * finalValue);
                    
                    if (isFloat) {
                        targetEl.innerText = currentVal.toFixed(2);
                    } else {
                        targetEl.innerText = Math.floor(currentVal);
                    }
                    
                    if (progress < 1) {
                        window.requestAnimationFrame(step);
                    } else {
                        targetEl.innerText = isFloat ? finalValue.toFixed(2) : finalValue;
                    }
                };
                window.requestAnimationFrame(step);
                observer.unobserve(targetEl);
            } else if (entry.isIntersecting) {
                // Reduced motion fallback
                const finalValue = parseFloat(entry.target.getAttribute('data-value'));
                const isFloat = finalValue % 1 !== 0 || entry.target.getAttribute('data-is-float') === 'true';
                entry.target.innerText = isFloat ? finalValue.toFixed(2) : finalValue;
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    statCounters.forEach(counter => {
        counter.innerText = "0" + (counter.getAttribute('data-is-float') === 'true' ? ".00" : "");
        countUpObserver.observe(counter);
    });

    // 4. Scroll Reveal & Progress Bars
    const revealElements = document.querySelectorAll('.reveal-on-scroll');
    const scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                
                // If it contains progress bars
                const pbFills = entry.target.querySelectorAll('.progress-bar-fill');
                pbFills.forEach(fill => {
                    fill.style.width = fill.getAttribute('data-width') + '%';
                });

                // If it contains Readiness Circle
                const circleProgress = entry.target.querySelector('.progress-circle');
                if (circleProgress) {
                    const score = parseInt(circleProgress.getAttribute('data-score'));
                    // 440 is the stroke-dasharray (circumference of r=70)
                    const offset = 440 - (440 * score) / 100;
                    setTimeout(() => {
                        circleProgress.style.strokeDashoffset = offset;
                    }, 300);
                }
                
                scrollObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: "0px 0px -50px 0px" });

    revealElements.forEach(el => scrollObserver.observe(el));

});
