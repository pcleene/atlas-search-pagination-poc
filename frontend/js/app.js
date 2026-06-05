/**
 * Automotive Parts Catalog Search - Main Application Logic
 */

class PartsSearchApp {
    constructor() {
        this.currentSearchParams = {
            searchText: '',
            sortBy: 'price',
            sortOrder: 'asc',
            limit: 20,
            filters: {
                seller: [],
                condition: [],
                location: []
            }
        };
        this.currentCursor = null;
        this.nextCursor = null;
        this.prevCursor = null;
        this.hasMore = false;
        this.facets = [];
        this.searchTimeout = null;

        this.init();
    }

    /**
     * Initialize the application
     */
    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', (e) => this.handleSearchInput(e));
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // Clear search
        const clearSearch = document.getElementById('clearSearch');
        clearSearch.addEventListener('click', () => this.clearSearch());

        // Sort and rows per page
        document.getElementById('sortBy').addEventListener('change', (e) => {
            this.handleSortChange(e);
        });
        document.getElementById('rowsPerPage').addEventListener('change', (e) => {
            this.currentSearchParams.limit = parseInt(e.target.value);
            this.performSearch(true);
        });

        // Filter button
        document.getElementById('filterBtn').addEventListener('click', () => {
            this.toggleFilterPanel();
        });
        document.getElementById('closeFilters').addEventListener('click', () => {
            this.toggleFilterPanel();
        });

        // Filter actions
        document.getElementById('applyFilters').addEventListener('click', () => {
            this.applyFilters();
        });
        document.getElementById('clearFilters').addEventListener('click', () => {
            this.clearAllFilters();
        });

        // Pagination
        document.getElementById('prevPage').addEventListener('click', () => {
            this.goToPreviousPage();
        });
        document.getElementById('nextPage').addEventListener('click', () => {
            this.goToNextPage();
        });
    }

    /**
     * Handle search input with debouncing
     */
    handleSearchInput(e) {
        const value = e.target.value;
        const clearBtn = document.getElementById('clearSearch');

        // Show/hide clear button
        clearBtn.style.display = value ? 'flex' : 'none';

        // Debounce search
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.currentSearchParams.searchText = value;
            if (value.length >= 2) {
                this.showAutocomplete(value);
            } else {
                this.hideAutocomplete();
                if (value.length === 0) {
                    this.performSearch(true);
                }
            }
        }, 300);
    }

    /**
     * Show autocomplete suggestions
     */
    async showAutocomplete(query) {
        try {
            const suggestions = await partsAPI.getAutocompleteSuggestions(query);
            const container = document.getElementById('autocompleteResults');

            if (suggestions.length === 0) {
                this.hideAutocomplete();
                return;
            }

            container.innerHTML = suggestions.map(item => `
                <div class="autocomplete-item" data-part="${item.partNo}">
                    <strong>${this.highlightMatch(item.partNo, query)}</strong> - ${item.name}
                </div>
            `).join('');

            // Add click handlers
            container.querySelectorAll('.autocomplete-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    const partNo = e.currentTarget.dataset.part;
                    document.getElementById('searchInput').value = partNo;
                    this.currentSearchParams.searchText = partNo;
                    this.hideAutocomplete();
                    this.performSearch(true);
                });
            });

            container.style.display = 'block';
        } catch (error) {
            console.error('Error showing autocomplete:', error);
        }
    }

    /**
     * Hide autocomplete
     */
    hideAutocomplete() {
        document.getElementById('autocompleteResults').style.display = 'none';
    }

    /**
     * Highlight matching text
     */
    highlightMatch(text, query) {
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }

    /**
     * Clear search
     */
    clearSearch() {
        document.getElementById('searchInput').value = '';
        document.getElementById('clearSearch').style.display = 'none';
        this.currentSearchParams.searchText = '';
        this.hideAutocomplete();
        this.performSearch(true);
    }

    /**
     * Handle sort change
     */
    handleSortChange(e) {
        const value = e.target.value;
        const [field, order] = value.split('-');

        this.currentSearchParams.sortBy = field;
        this.currentSearchParams.sortOrder = order;

        this.performSearch(true);
    }

    /**
     * Toggle filter panel
     */
    toggleFilterPanel() {
        const panel = document.getElementById('filterPanel');
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }

    /**
     * Apply filters
     */
    applyFilters() {
        // Collect checked filters
        const filters = {
            seller: [],
            condition: [],
            location: []
        };

        document.querySelectorAll('#sellerFilters input:checked').forEach(cb => {
            filters.seller.push(cb.value);
        });
        document.querySelectorAll('#conditionFilters input:checked').forEach(cb => {
            filters.condition.push(cb.value);
        });
        document.querySelectorAll('#locationFilters input:checked').forEach(cb => {
            filters.location.push(cb.value);
        });

        this.currentSearchParams.filters = filters;
        this.toggleFilterPanel();
        this.performSearch(true);
    }

    /**
     * Clear all filters
     */
    clearAllFilters() {
        document.querySelectorAll('#filterPanel input[type="checkbox"]').forEach(cb => {
            cb.checked = false;
        });
        this.currentSearchParams.filters = {
            seller: [],
            condition: [],
            location: []
        };
        this.performSearch(true);
    }

    /**
     * Perform search
     */
    async performSearch(resetPagination = false) {
        if (resetPagination) {
            this.currentCursor = null;
        }

        this.showLoading();
        this.hideAutocomplete();

        try {
            const response = await partsAPI.searchParts({
                searchText: this.currentSearchParams.searchText,
                sortBy: this.currentSearchParams.sortBy,
                sortOrder: this.currentSearchParams.sortOrder,
                limit: this.currentSearchParams.limit,
                cursor: this.currentCursor,
                seller: this.currentSearchParams.filters.seller,
                condition: this.currentSearchParams.filters.condition,
                location: this.currentSearchParams.filters.location
            });

            if (!response) {
                return; // Request was cancelled
            }

            this.renderResults(response);
            this.updatePagination(response.pagination);
            this.updateFacets(response.facets);

        } catch (error) {
            console.error('Search error:', error);
            this.showError('Failed to load parts. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Load initial data
     */
    async loadInitialData() {
        await this.performSearch(true);
    }

    /**
     * Render search results
     */
    renderResults(response) {
        const container = document.getElementById('partsListing');
        const { parts } = response;

        // Remove loading and empty states
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';

        if (parts.length === 0) {
            document.getElementById('emptyState').style.display = 'block';
            return;
        }

        container.innerHTML = parts.map(part => this.createPartCard(part)).join('');
    }

    /**
     * Create HTML for a part card
     */
    createPartCard(part) {
        return `
            <div class="part-card">
                <div class="part-header">
                    <div class="part-title">
                        <div class="part-number">${part.part_no}</div>
                        <div class="part-name">${part.name}</div>
                    </div>
                    <div class="part-price">
                        ${part.local_currency} ${part.local_markup_price.toFixed(2)}
                    </div>
                </div>
                <div class="part-body">
                    <div class="part-icon">📦</div>
                    <div class="part-details">
                        <div class="detail-item">
                            <span class="detail-label">Quantity available</span>
                            <span class="detail-value">${part.stock} (Each)</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Batch No</span>
                            <span class="detail-value">${part.batch_no || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Part's Location</span>
                            <span class="detail-value">${part.location}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Seller</span>
                            <span class="detail-value">${part.seller_company}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Condition</span>
                            <span class="detail-value">${part.condition}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Material Class</span>
                            <span class="detail-value">${part.material_class}</span>
                        </div>
                    </div>
                    <div class="part-actions">
                        <div class="quantity-selector">
                            <label class="quantity-label">Select Quantity</label>
                            <input type="number" class="quantity-input" value="1" min="1" max="${part.stock}">
                        </div>
                        <button class="add-to-cart-btn">🛒 Add to Cart</button>
                    </div>
                </div>
                <div class="part-footer">
                    Last updated: ${new Date(part.updated_at).toLocaleDateString()}.
                    Please <a href="#" class="seller-link">Ask ${part.seller_company}</a> for more information.
                </div>
            </div>
        `;
    }

    /**
     * Update pagination controls
     */
    updatePagination(pagination) {
        const { has_more, next_cursor, prev_cursor, current_page_start, current_page_end, total_count } = pagination;

        this.nextCursor = next_cursor;
        this.prevCursor = prev_cursor;
        this.hasMore = has_more;

        const paginationEl = document.getElementById('pagination');
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        const pageInfo = document.getElementById('pageInfo');

        // Show/hide pagination
        paginationEl.style.display = (next_cursor || prev_cursor) ? 'flex' : 'none';

        // Update button states
        prevBtn.disabled = !prev_cursor;
        nextBtn.disabled = !has_more;

        // Update page info
        const totalText = total_count ? ` of ${total_count}` : '';
        pageInfo.textContent = `Showing ${current_page_start}-${current_page_end}${totalText}`;
    }

    /**
     * Update facets in filter panel
     */
    updateFacets(facets) {
        this.facets = facets;

        facets.forEach(facet => {
            const containerId = `${facet.field}Filters`;
            const container = document.getElementById(containerId);

            if (!container) return;

            container.innerHTML = facet.buckets.map(bucket => `
                <div class="filter-option">
                    <input type="checkbox" id="${facet.field}-${bucket.value}" value="${bucket.value}">
                    <label for="${facet.field}-${bucket.value}">
                        ${bucket.value} <span class="count">(${bucket.count})</span>
                    </label>
                </div>
            `).join('');
        });
    }

    /**
     * Go to next page
     */
    goToNextPage() {
        if (this.nextCursor) {
            this.currentCursor = this.nextCursor;
            this.performSearch(false);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    /**
     * Go to previous page
     */
    goToPreviousPage() {
        if (this.prevCursor) {
            this.currentCursor = this.prevCursor;
            this.performSearch(false);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    /**
     * Show loading state
     */
    showLoading() {
        document.getElementById('loadingState').style.display = 'block';
        document.getElementById('emptyState').style.display = 'none';
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        document.getElementById('loadingState').style.display = 'none';
    }

    /**
     * Show error message
     */
    showError(message) {
        const container = document.getElementById('partsListing');
        container.innerHTML = `
            <div class="empty-state">
                <p style="color: var(--danger-color);">${message}</p>
            </div>
        `;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.partsSearchApp = new PartsSearchApp();
});
