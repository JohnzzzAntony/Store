/* ============================================================
   SALEEL PARFUMS — Cart JavaScript
   Handles AJAX add/remove cart actions for all pages
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
  var updateBtns = document.querySelectorAll('.update-cart');

  updateBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var productId = this.dataset.product;
      var action    = this.dataset.action;
      var quantity  = this.dataset.quantity ? parseInt(this.dataset.quantity) : 1;

      if (isAuthenticated === true || isAuthenticated === 'true') {
        updateServerCart(productId, action, quantity);
      } else {
        updateCookieCart(productId, action, quantity);
      }
    });
  });

  function updateServerCart(productId, action, quantity = 1) {
    fetch('/update_item/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
      },
      body: JSON.stringify({ productId: productId, action: action, quantity: quantity }),
    })
      .then(function (res) { return res.json(); })
      .then(function () {
        // Sync to Firebase for real-time analytics
        if (window.firestoreDB && window.firebaseAuth && window.firebaseAuth.currentUser) {
          const { doc, setDoc, serverTimestamp } = window.firebaseModule;
          const activityRef = doc(window.firestoreDB, "cart_activities", Date.now().toString());
          setDoc(activityRef, {
            user_uid: window.firebaseAuth.currentUser.uid,
            product_id: productId,
            action: action,
            timestamp: serverTimestamp()
          }).then(() => {
            location.reload();
          });
        } else {
          location.reload();
        }
      })
      .catch(function (err) {
        console.error('Cart update error:', err);
      });
  }

  function updateCookieCart(productId, action, quantity = 1) {
    if (!cart) cart = {};
    if (cart[productId] === undefined) {
      cart[productId] = { quantity: 0 };
    }

    if (action === 'add') {
      cart[productId]['quantity'] += quantity;
    } else if (action === 'remove') {
      cart[productId]['quantity'] -= 1;
      if (cart[productId]['quantity'] <= 0) {
        delete cart[productId];
      }
    }

    document.cookie = 'cart=' + JSON.stringify(cart) + ';domain=;path=/';
    location.reload();
  }
});
