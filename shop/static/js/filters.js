(function () {
    'use strict';

    const form = document.getElementById('filter-form');
    const results = document.getElementById('product-results');
    if (!form || !results) return;

    let controller = null;   // برای لغو درخواست قبلی
    let timer = null;        // برای debounce فیلد قیمت

    // آدرس صفحه‌ی فعلی + پارامترهای پر فرم (فیلدهای خالی حذف می‌شن)
    function buildUrl() {
        const params = new URLSearchParams();
        new FormData(form).forEach((value, key) => {
            if (String(value).trim() !== '') params.append(key, value);
        });
        const qs = params.toString();
        return location.pathname + (qs ? '?' + qs : '');
    }

    async function load(url, push) {
        if (controller) controller.abort();
        const mine = new AbortController();
        controller = mine;

        results.classList.add('is-loading');
        results.setAttribute('aria-busy', 'true');

        try {
            const response = await fetch(url, {
                headers: {'X-Requested-With': 'XMLHttpRequest'},
                credentials: 'same-origin',
                signal: mine.signal,
            });
            if (!response.ok) throw new Error('HTTP ' + response.status);

            results.innerHTML = await response.text();
            if (push) history.pushState(null, '', url);
        } catch (err) {
            if (err.name === 'AbortError') return;   // درخواست جدیدتری جایگزینش شده
            console.error(err);
            window.location.href = url;              // اگر خطا شد، بارگذاری عادی صفحه
        } finally {
            if (controller === mine) {
                results.classList.remove('is-loading');
                results.removeAttribute('aria-busy');
            }
        }
    }

    function applyFilters() {
        clearTimeout(timer);
        load(buildUrl(), true);
    }

    // مقدار فرم را با آدرس فعلی هماهنگ می‌کند (دکمه‌ی برگشت مرورگر)
    function syncForm() {
        const p = new URLSearchParams(location.search);
        form.elements['min_price'].value = p.get('min_price') || '';
        form.elements['max_price'].value = p.get('max_price') || '';
        form.elements['in_stock'].checked = p.get('in_stock') === '1';
    }

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        applyFilters();
    });

    // کنترل‌های فرم (حتی select مرتب‌سازی که بیرون فرم است ولی form="filter-form" دارد)
    document.addEventListener('change', (event) => {
        if (event.target.form === form) applyFilters();
    });

    document.addEventListener('input', (event) => {
        if (event.target.form === form && event.target.type === 'number') {
            clearTimeout(timer);
            timer = setTimeout(applyFilters, 600);
        }
    });

    // صفحه‌بندی: به‌جای بارگذاری کامل، فقط نتایج عوض می‌شن
    results.addEventListener('click', (event) => {
        const link = event.target.closest('.pagination a.page-link');
        if (!link) return;

        event.preventDefault();
        load(link.href, true);
        results.scrollIntoView({behavior: 'smooth', block: 'start'});
    });

    // حذف فیلترها (دکمه‌ی کنار فرم و دکمه‌ی «محصولی پیدا نشد»)
    document.addEventListener('click', (event) => {
        if (!event.target.closest('[data-filter-reset]')) return;

        form.elements['min_price'].value = '';
        form.elements['max_price'].value = '';
        form.elements['in_stock'].checked = false;
        applyFilters();
    });

    window.addEventListener('popstate', () => {
        syncForm();
        load(location.href, false);
    });
})();
