// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    // Login Form Handler
    const loginForm = document.getElementById('loginform');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Signup Form Handler
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
});

// Login Function
async function handleLogin(e) {
    e.preventDefault();
    const form = e.target;
    const email = form.email.value.trim().toLowerCase();
    const password = form.password.value;
    const errorElement = document.getElementById('errorMessage');

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Login failed');
        }

        if (data.success) {
            localStorage.setItem('currentUser', JSON.stringify(data.user));
            window.location.href = '/';
        } else {
            errorElement.textContent = data.message || 'Invalid credentials';
            form.password.value = '';
        }
    } catch (error) {
        console.error('Login error:', error);
        errorElement.textContent = error.message || 'Login failed. Please try again.';
    }
}

// Signup Function
document.getElementById('signup-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const fullname = document.getElementById('fullname').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const errorMessage = document.getElementById('errorMessage');
    
    // Clear error
    errorMessage.textContent = '';

    // Basic validations
    if (!fullname || !email || !password || !confirmPassword) {
        errorMessage.textContent = 'All fields are required.';
        return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        errorMessage.textContent = 'Invalid email format.';
        return;
    }

    const strongPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$/;

if (!strongPasswordRegex.test(password)) {
    errorMessage.textContent = 'Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.';
    return;
}

    if (password !== confirmPassword) {
        errorMessage.textContent = 'Passwords do not match.';
        return;
    }

    try {
        const response = await fetch('/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ fullname, email, password })
        });

        const result = await response.json();
        if (result.success) {
            alert('Signup successful!');
            window.location.href = '/login';
        } else {
            errorMessage.textContent = result.message || 'Signup failed.';
        }
    } catch (error) {
        errorMessage.textContent = 'An error occurred. Please try again.';
    }
});


// Logout Function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        fetch('/logout', { method: 'GET' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    localStorage.removeItem('currentUser');
                    window.location.href = '/login';
                } else {
                    alert('Logout failed. Please try again.');
                }
            })
            .catch(error => {
                console.error('Logout error:', error);
                alert('Logout failed. Please try again.');
            });
    }
}

// Insightify - Interactive JavaScript

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                window.scrollTo({
                    top: target.offsetTop - 80, // Offset for the fixed header
                    behavior: 'smooth'
                });
            }
        });
    });

    // Add scroll animation for elements
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.purpose, .cta, .testimonials, .did-you-know, .resources, .fact, .testimonial');
        
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;
            
            if (elementTop < window.innerHeight - elementVisible) {
                element.classList.add('visible');
            }
        });
    };

    // Add CSS for the animation
    const style = document.createElement('style');
    style.textContent = `
        .purpose, .cta, .testimonials, .did-you-know, .resources, .fact, .testimonial {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        .visible {
            opacity: 1;
            transform: translateY(0);
        }
    `;
    document.head.appendChild(style);

    // Call the animation function on page load and scroll
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Initial check on page load
    
    // Logout function
    window.logout = function() {
        // You can replace this with actual logout logic
        if (confirm('Are you sure you want to log out?')) {
            // Redirect to logout URL or handle logout
            alert('Logged out successfully!');
            window.location.href = "/login"; // Redirect to login page
        }
    };
    
    // Add active class to current navigation item
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('nav ul li a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });
    
    // Add CSS for active navigation
    const activeStyle = document.createElement('style');
    activeStyle.textContent = `
        nav ul li a.active {
            color: #F4A460;
        }
        nav ul li a.active:after {
            width: 100%;
        }
    `;
    document.head.appendChild(activeStyle);
    
    // Testimonial carousel for mobile
    if (window.innerWidth < 768) {
        const testimonials = document.querySelectorAll('.testimonial');
        let currentTestimonial = 0;
        
        // Hide all testimonials except the first one
        testimonials.forEach((testimonial, index) => {
            if (index !== 0) {
                testimonial.style.display = 'none';
            }
        });
        
        // Create navigation dots
        const dotsContainer = document.createElement('div');
        dotsContainer.className = 'testimonial-dots';
        dotsContainer.style.cssText = 'text-align: center; margin-top: 20px;';
        
        testimonials.forEach((_, index) => {
            const dot = document.createElement('span');
            dot.style.cssText = 'display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: ' + 
                (index === 0 ? '#2E8B57' : '#ccc') + '; margin: 0 5px; cursor: pointer; transition: background-color 0.3s ease;';
            dot.addEventListener('click', () => showTestimonial(index));
            dotsContainer.appendChild(dot);
        });
        
        if (testimonials.length > 0) {
            testimonials[0].parentNode.appendChild(dotsContainer);
        }
        
        function showTestimonial(index) {
            // Hide current testimonial
            testimonials[currentTestimonial].style.display = 'none';
            dotsContainer.children[currentTestimonial].style.backgroundColor = '#ccc';
            
            // Show selected testimonial
            currentTestimonial = index;
            testimonials[currentTestimonial].style.display = 'flex';
            dotsContainer.children[currentTestimonial].style.backgroundColor = '#2E8B57';
        }
        
        // Auto-rotate testimonials
        setInterval(() => {
            const nextIndex = (currentTestimonial + 1) % testimonials.length;
            showTestimonial(nextIndex);
        }, 5000);
    }
});

