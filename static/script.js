document.addEventListener('DOMContentLoaded', () => {
    const bodyId = document.body.id;
  
    if (bodyId === 'home') {
      console.log('Home page script running');
      // call home page functions here
    }
  
    if (bodyId === 'login-page') {
      console.log('Login page script running');
      // call login-specific functions here
    }
  });