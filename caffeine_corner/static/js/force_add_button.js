// Force show Add button on empty Unfold changelist
document.addEventListener('DOMContentLoaded', function() {
    const addBtn = document.querySelector('a[href*="/add/"]');
    if (addBtn) {
        addBtn.style.display = 'flex';
    }
    
    // If no add button exists, create one
    const toolbar = document.querySelector('.unfold-toolbar') 
                 || document.querySelector('[class*="toolbar"]')
                 || document.querySelector('header');
    
    if (toolbar && !document.querySelector('a[href*="/add/"]')) {
        const currentUrl = window.location.href.replace(/\/$/, '');
        const addUrl     = currentUrl + '/add/';
        const btn = document.createElement('a');
        btn.href      = addUrl;
        btn.innerText = '+ Add Ingredient';
        btn.className = 'btn'; 
        toolbar.appendChild(btn);
    }
});

