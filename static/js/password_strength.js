document.addEventListener('DOMContentLoaded', function() {
    // Find password inputs
    const passInputs = document.querySelectorAll('input[type="password"]');
    
    // We only want to attach this to actual primary password fields, not confirmation ones.
    // In Django, login is "password", register is "password1" (and confirm is "password2").
    passInputs.forEach(input => {
        if (input.name === 'password' || input.name === 'password1') {
            attachPasswordStrengthIndicator(input);
        }
    });

    function attachPasswordStrengthIndicator(input) {
        // Create indicator container
        const container = document.createElement('div');
        container.className = 'mt-2 text-xs transition-all duration-300';
        container.style.display = 'none';

        const header = document.createElement('div');
        header.className = 'flex justify-between items-center mb-1';
        
        const label = document.createElement('span');
        label.className = 'text-slate-400';
        label.innerText = 'Password Strength: ';

        const statusText = document.createElement('span');
        statusText.className = 'font-bold';
        
        header.appendChild(label);
        header.appendChild(statusText);

        const barContainer = document.createElement('div');
        barContainer.className = 'h-1.5 w-full bg-slate-800 rounded-full overflow-hidden';
        
        const bar = document.createElement('div');
        bar.className = 'h-full w-0 transition-all duration-300';
        barContainer.appendChild(bar);

        const suggestion = document.createElement('p');
        suggestion.className = 'mt-1.5 text-slate-400';
        
        const suggestionText = document.createElement('span');
        
        const useBtn = document.createElement('button');
        useBtn.type = 'button';
        useBtn.className = 'ml-1 text-indigo-400 hover:text-indigo-300 underline font-medium';
        useBtn.innerText = 'Use suggested password';
        
        suggestion.appendChild(suggestionText);
        suggestion.appendChild(useBtn);

        container.appendChild(header);
        container.appendChild(barContainer);
        container.appendChild(suggestion);

        // Insert right after the input's parent wrapper (relative div for eye icon)
        input.parentElement.insertAdjacentElement('afterend', container);

        function generateStrongPassword() {
            const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+";
            let pass = "";
            for (let i = 0; i < 16; i++) {
                pass += chars.charAt(Math.floor(Math.random() * chars.length));
            }
            return pass;
        }

        let currentSuggested = "";

        useBtn.addEventListener('click', function() {
            input.value = currentSuggested;
            // If it's a register form, also fill password 2
            const confirmInput = document.getElementById('id_password2');
            if (confirmInput) {
                confirmInput.value = currentSuggested;
            }
            // Trigger input event to re-evaluate strength
            input.dispatchEvent(new Event('input'));
            
            // Unmask the password to show the user what was generated
            input.type = 'text';
            const eyeIcon = input.parentElement.querySelector('[data-lucide]');
            if (eyeIcon) {
                eyeIcon.setAttribute('data-lucide', 'eye-off');
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        });

        input.addEventListener('input', function() {
            const val = input.value;
            if (val.length === 0) {
                container.style.display = 'none';
                return;
            }
            container.style.display = 'block';

            let score = 0;
            if (val.length > 7) score += 1;
            if (val.length > 10) score += 1;
            if (/[A-Z]/.test(val)) score += 1;
            if (/[0-9]/.test(val)) score += 1;
            if (/[^A-Za-z0-9]/.test(val)) score += 1;

            if (score < 3) {
                statusText.innerText = 'Weak';
                statusText.className = 'font-bold text-red-500';
                bar.style.width = '33%';
                bar.className = 'h-full transition-all duration-300 bg-red-500';
                
                currentSuggested = generateStrongPassword();
                suggestionText.innerHTML = 'Your password is <span class="text-red-400 font-bold">Weak</span>. We suggest you change it to a strong password: <span class="font-mono bg-slate-800 px-1 py-0.5 rounded text-slate-300">' + currentSuggested + '</span>';
                suggestion.style.display = 'block';
            } else if (score === 3 || score === 4) {
                statusText.innerText = 'Normal';
                statusText.className = 'font-bold text-orange-400';
                bar.style.width = '66%';
                bar.className = 'h-full transition-all duration-300 bg-orange-400';
                
                currentSuggested = generateStrongPassword();
                suggestionText.innerHTML = 'Your password is <span class="text-orange-400 font-bold">Normal</span>. Make it stronger, or use: <span class="font-mono bg-slate-800 px-1 py-0.5 rounded text-slate-300">' + currentSuggested + '</span>';
                suggestion.style.display = 'block';
            } else {
                statusText.innerText = 'Strong';
                statusText.className = 'font-bold text-emerald-500';
                bar.style.width = '100%';
                bar.className = 'h-full transition-all duration-300 bg-emerald-500';
                suggestion.style.display = 'none';
            }
        });
    }
});
