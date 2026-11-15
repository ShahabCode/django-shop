(function () {
    'use strict';

    const faNum = (n) => Number(n).toLocaleString('fa-IR');

    // ---------- Helpers ----------
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta && meta.content) return meta.content;

        const cookie = document.cookie.split('; ').find((row) => row.startsWith('csrftoken='));
        return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
    }

    function post(url, data) {
        return fetch(url, {
            method: 'POST',
            headers: {'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest'},
            body: new URLSearchParams(data),
            credentials: 'same-origin',
        }).then((response) => {
            if (!response.ok) throw new Error('HTTP ' + response.status);
            return response.json();
        });
    }

    // پیام کوچک پایین صفحه (بدون وابستگی به bootstrap.js)
    function toast(message, type, linkHref, linkText) {
        let box = document.getElementById('toast-box');
        if (!box) {
            box = document.createElement('div');
            box.id = 'toast-box';
            box.className = 'toast-container position-fixed bottom-0 start-0 p-3';
            document.body.appendChild(box);
        }

        const el = document.createElement('div');
        el.className = 'toast align-items-center border-0 text-bg-' + (type || 'success');
        el.setAttribute('role', 'alert');
        el.innerHTML =
            '<div class="d-flex">' +
            '<div class="toast-body"></div>' +
            '<button type="button" class="btn-close btn-close-white ms-2 m-auto" aria-label="بستن"></button>' +
            '</div>';

        const body = el.querySelector('.toast-body');
        body.textContent = message;

        if (linkHref) {
            const link = document.createElement('a');
            link.href = linkHref;
            link.textContent = linkText || 'مشاهده';
            link.className = 'text-white fw-bold ms-2';
            body.appendChild(link);
        }

        box.appendChild(el);
        el.classList.add('show');

        const remove = () => el.remove();
        el.querySelector('.btn-close').addEventListener('click', remove);
        setTimeout(remove, 3500);
    }

    function setText(selector, value) {
        document.querySelectorAll(selector).forEach((el) => {
            el.textContent = faNum(value);
        });
    }

    // به‌روزرسانی badge سبد، جمع کل و مبالغ (navbar، ساید بار و صفحه‌ی سبد)
    function updateCart(data) {
        document.body.dataset.cartCount = data.item_count;

        document.querySelectorAll('[data-cart-count]').forEach((el) => {
            if (el === document.body) return;  // <body> فقط تعداد را نگه می‌دارد، متنش نباید عوض شود
            el.textContent = faNum(data.item_count);
            el.classList.toggle('d-none', !data.item_count);
        });
        setText('[data-items-count]', data.item_count);
        setText('[data-cart-total]', data.total_price);

        if ('post_price' in data) setText('[data-post-price]', data.post_price);
        if ('final_price' in data) setText('[data-final-price]', data.final_price);
    }

    // ---------- ساید بار سبد خرید (سمت چپ صفحه) ----------
    function getMiniCartEl() {
        let el = document.getElementById('mini-cart-offcanvas');

        if (!el) {
            el = document.createElement('div');
            el.id = 'mini-cart-offcanvas';
            el.className = 'offcanvas offcanvas-end';
            el.tabIndex = -1;
            el.setAttribute('aria-labelledby', 'mini-cart-title');
            el.innerHTML =
                '<div class="offcanvas-header border-bottom">' +
                '<h5 class="offcanvas-title" id="mini-cart-title"><i class="bi bi-cart3 me-2"></i>سبد خرید</h5>' +
                '<button type="button" class="btn-close" data-bs-dismiss="offcanvas" aria-label="بستن"></button>' +
                '</div>' +
                '<div class="offcanvas-body p-0"></div>';
            document.body.appendChild(el);
        }

        return el;
    }

    function openMiniCart(html) {
        if (!window.bootstrap) return false;

        const el = getMiniCartEl();
        el.querySelector('.offcanvas-body').innerHTML = html;
        bootstrap.Offcanvas.getOrCreateInstance(el).show();
        return true;
    }

    const EMPTY_MINI_CART =
        '<div class="text-center my-auto px-3">' +
        '<i class="bi bi-cart-x display-3 text-muted"></i>' +
        '<p class="mt-3">سبد خرید شما خالی است.</p>' +
        '<button type="button" class="btn btn-outline-primary" data-bs-dismiss="offcanvas">ادامه خرید</button>' +
        '</div>';

    // ---------- افزودن به سبد (لیست و جزئیات محصول) ----------
    document.addEventListener('click', async (event) => {
        const btn = event.target.closest('[data-add-to-cart]');
        if (!btn) return;

        const prevCount = Number(document.body.dataset.cartCount || 0);
        btn.disabled = true;

        try {
            const data = await post(btn.dataset.url, {});
            if (data.error) throw new Error(data.error);

            updateCart(data);

            const opened = data.html ? openMiniCart(data.html) : false;

            if (data.item_count === prevCount) {
                toast('به حداکثر موجودی این محصول رسیده‌اید', 'warning');
            } else if (!opened) {
                const cartLink = document.querySelector('a[aria-label="سبد خرید"]');
                toast('محصول به سبد خرید اضافه شد', 'success',
                      cartLink ? cartLink.href : null, 'مشاهده سبد');
            }
        } catch (err) {
            console.error(err);
            toast('خطا در افزودن به سبد خرید: ' + err.message, 'danger');
        } finally {
            btn.disabled = false;
        }
    });

    // ---------- افزایش / کاهش / حذف (هم صفحه‌ی سبد هم ساید بار) ----------
    document.addEventListener('click', async (event) => {
        const btn = event.target.closest('[data-cart-action]');
        if (!btn) return;

        const row = btn.closest('[data-item-id]');
        const root = btn.closest('[data-update-url]');
        if (!row || !root) return;

        const itemId = row.dataset.itemId;
        const action = btn.dataset.cartAction;
        const prevQty = Number(row.dataset.qty);

        btn.disabled = true;

        try {
            const data = action === 'remove'
                ? await post(root.dataset.removeUrl, {item_id: itemId})
                : await post(root.dataset.updateUrl, {item_id: itemId, action: action});

            if (!data.success) throw new Error(data.error);

            updateCart(data);

            if (action === 'remove') {
                row.remove();

                if (!data.item_count) {
                    if (root.id === 'cart-page') {
                        location.reload();  // نمایش حالت «سبد خالی»
                    } else {
                        root.innerHTML = EMPTY_MINI_CART;
                    }
                    return;
                }
            } else {
                row.dataset.qty = data.quantity;
                row.querySelector('[data-qty-text]').textContent = faNum(data.quantity);
                row.querySelector('[data-line-total]').textContent = faNum(data.total);

                if (action === 'add' && data.quantity === prevQty) {
                    toast('به حداکثر موجودی این محصول رسیده‌اید', 'warning');
                }
            }
        } catch (err) {
            console.error(err);
            toast('خطا در به‌روزرسانی سبد خرید: ' + err.message, 'danger');
        } finally {
            btn.disabled = false;

            if (row.isConnected) {
                const minus = row.querySelector('[data-cart-action="decrease"]');
                if (minus) minus.disabled = Number(row.dataset.qty) <= 1;
            }
        }
    });

    // ---------- گالری تصاویر (جزئیات محصول) ----------
    document.addEventListener('click', (event) => {
        const thumb = event.target.closest('[data-gallery-thumb]');
        if (!thumb) return;

        const main = document.getElementById('main-image');
        if (main) main.src = thumb.dataset.src;

        document.querySelectorAll('[data-gallery-thumb]').forEach((el) => {
            el.classList.toggle('active', el === thumb);
        });
    });
})();
