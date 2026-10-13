document.addEventListener('DOMContentLoaded', () => {
    
    // --- Navigation Logic ---
    const navLinks = document.querySelectorAll('.nav-links a');
    const navTriggers = document.querySelectorAll('.nav-trigger');
    const screens = document.querySelectorAll('.screen');

    function navigateTo(targetId) {
        // Update active nav link
        navLinks.forEach(link => {
            if (link.getAttribute('data-target') === targetId) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Show target screen
        screens.forEach(screen => {
            if (screen.id === targetId) {
                screen.classList.add('active');
            } else {
                screen.classList.remove('active');
            }
        });
    }

    // Attach click events to sidebar links
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = link.getAttribute('data-target');
            navigateTo(target);
        });
    });

    // Attach click events to buttons acting as nav triggers (e.g. from Overview)
    navTriggers.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const target = btn.getAttribute('data-target');
            navigateTo(target);
        });
    });

    // --- Theme Switcher Logic ---
    const themeSelect = document.getElementById('theme-select');
    themeSelect.addEventListener('change', (e) => {
        const theme = e.target.value;
        // Remove existing theme classes
        document.body.classList.remove('theme-concept-1', 'theme-concept-2', 'theme-concept-3');
        // Add selected theme class
        document.body.classList.add(theme);
    });

    // --- Form Simulation Logic ---
    
    function simulatePrediction(prefix, callback) {
        const emptyState = document.getElementById(`${prefix}-empty`);
        const loadingState = document.getElementById(`${prefix}-loading`);
        const resultState = document.getElementById(`${prefix}-result`);

        // Hide empty and result, show loading
        emptyState.classList.remove('active');
        resultState.classList.remove('active');
        loadingState.classList.add('active');

        // Simulate network delay
        setTimeout(() => {
            loadingState.classList.remove('active');
            resultState.classList.add('active');
            if(callback) callback();
        }, 1500);
    }

    // Zeta Potential Form
    const zetaForm = document.getElementById('zeta-form');
    if(zetaForm) {
        zetaForm.addEventListener('submit', (e) => {
            e.preventDefault();
            simulatePrediction('zeta', () => {
                // Here we could update the result dynamically based on inputs, 
                // but static demo values are sufficient per requirements.
                console.log("Mock Zeta Potential prediction complete.");
            });
        });
    }

    // Cytotoxicity Form
    const cytoForm = document.getElementById('cyto-form');
    if(cytoForm) {
        cytoForm.addEventListener('submit', (e) => {
            e.preventDefault();
            simulatePrediction('cyto', () => {
                console.log("Mock Cytotoxicity prediction complete.");
            });
        });
    }
});
