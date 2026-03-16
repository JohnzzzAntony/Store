/* ============================================================
   SALEEL PARFUMS — Main JavaScript
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

  // ---- Header scroll effect ----
  var header = document.getElementById('siteHeader');
  if (header) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 40) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    });
  }

  // ---- Menu Toggle (Burger → Drawer) ----
  var menuToggle  = document.getElementById('menuToggle');
  var navDrawer   = document.getElementById('navDrawer');
  var drawerClose = document.getElementById('navDrawerClose');

  if (menuToggle && navDrawer) {
    menuToggle.addEventListener('click', function () {
      navDrawer.classList.add('open');
      menuToggle.classList.add('open');
      document.body.style.overflow = 'hidden';
    });
  }

  if (drawerClose && navDrawer) {
    drawerClose.addEventListener('click', function () {
      navDrawer.classList.remove('open');
      if (menuToggle) menuToggle.classList.remove('open');
      document.body.style.overflow = '';
    });
  }

  // Close drawer on nav link click
  if (navDrawer) {
    navDrawer.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navDrawer.classList.remove('open');
        if (menuToggle) menuToggle.classList.remove('open');
        document.body.style.overflow = '';
      });
    });
  }

  // ---- Auto-dismiss flash messages ----
  var messagesContainer = document.getElementById('messagesContainer');
  if (messagesContainer) {
    setTimeout(function () {
      messagesContainer.style.opacity = '0';
      messagesContainer.style.transform = 'translateX(120%)';
      messagesContainer.style.transition = 'all 0.4s ease';
      setTimeout(function () { messagesContainer.remove(); }, 400);
    }, 5000);
  }

  // ---- Product Wishlist Buttons (Cookie-based) ----
  document.querySelectorAll('.product-wishlist-btn').forEach(function (btn) {
    var productId = btn.id.replace('wishlist-', '').replace('plp-wish-', '');
    var wishlist  = getWishlist();

    if (wishlist.includes(productId)) {
      var icon = btn.querySelector('i');
      if (icon) {
        icon.classList.remove('ph-heart');
        icon.classList.add('ph-heart-fill');
        btn.style.color = '#e74c3c';
      }
    }

    btn.addEventListener('click', function () {
      var icon = btn.querySelector('i');
      wishlist = getWishlist();
      var idx = wishlist.indexOf(productId);

      if (idx === -1) {
        wishlist.push(productId);
        if (icon) {
          icon.classList.remove('ph-heart');
          icon.classList.add('ph-heart-fill');
          btn.style.color = '#e74c3c';
        }
      } else {
        wishlist.splice(idx, 1);
        if (icon) {
          icon.classList.remove('ph-heart-fill');
          icon.classList.add('ph-heart');
          btn.style.color = '';
        }
      }
      saveWishlist(wishlist);
    });
  });

  function getWishlist() {
    try {
      return JSON.parse(localStorage.getItem('saleel_wishlist') || '[]');
    } catch (e) { return []; }
  }
  function saveWishlist(list) {
    localStorage.setItem('saleel_wishlist', JSON.stringify(list));
  }

  // ---- Add to Cart Notification ----
  var addToCartBtns = document.querySelectorAll('.update-cart');
  addToCartBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      if (this.dataset.action === 'add') {
        showCartToast();
      }
    });
  });

  function showCartToast() {
    var toast = document.createElement('div');
    toast.className = 'alert alert-success';
    toast.innerHTML = '✓ Added to cart successfully';
    toast.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:3000;box-shadow:0 4px 20px rgba(0,0,0,0.15);border-left:4px solid #27ae60;background:#fff;padding:14px 20px;font-size:13px;min-width:220px;';
    document.body.appendChild(toast);
    setTimeout(function () {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(20px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(function () { toast.remove(); }, 300);
    }, 2500);
  }

  // ---- Search Overlay (simple redirect to products) ----
  var searchBtn = document.getElementById('searchBtn');
  if (searchBtn) {
    searchBtn.addEventListener('click', function(e) {
      // Already linked to product_list, but we can add a quick search
    });
  }

  // ---- Smooth reveal animation for product cards ----
  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.product-card, .blog-card').forEach(function (el) {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      observer.observe(el);
    });
  }

});
