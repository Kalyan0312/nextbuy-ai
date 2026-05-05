document.addEventListener('DOMContentLoaded', () => {
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    
    if (searchInput && searchResults) {
        let debounceTimer;
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                searchResults.style.display = 'none';
                return;
            }
            
            debounceTimer = setTimeout(() => {
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.length > 0) {
                            searchResults.innerHTML = data.map(product => `
                                <div style="padding: 1rem; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; gap: 1rem; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='var(--surface-hover)'" onmouseout="this.style.background='transparent'">
                                    <img src="${product.image_url}" alt="${product.name}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px;">
                                    <div>
                                        <div style="font-weight: 600; color: var(--text-primary);">${product.name}</div>
                                        <div style="font-size: 0.8rem; color: var(--accent-color);">${product.category} &bull; ₹${product.price}</div>
                                    </div>
                                </div>
                            `).join('');
                            searchResults.style.display = 'block';
                        } else {
                            searchResults.innerHTML = '<div style="padding: 1rem; text-align: center; color: var(--text-secondary);">No products found</div>';
                            searchResults.style.display = 'block';
                        }
                    })
                    .catch(err => console.error('Search error:', err));
            }, 300);
        });
        
        // Hide search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.style.display = 'none';
            }
        });
    }
});

function addToCart(productId) {
    const btn = event.currentTarget;
    const originalText = btn.innerHTML;
    
    fetch(`/add_to_cart/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            btn.innerHTML = '<i class="fa-solid fa-check"></i> Added';
            btn.style.background = '#10b981';
            
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.style.background = ''; // reset to CSS
            }, 2000);
        } else {
            alert(data.error || 'Failed to add product to cart');
        }
    })
    .catch(err => {
        console.error('Error adding to cart:', err);
        alert('An error occurred. Please try again.');
    });
}
