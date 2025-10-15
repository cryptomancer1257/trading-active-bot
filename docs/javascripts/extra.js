// QuantumForge Documentation - Custom JavaScript

// Add copy button functionality
document.addEventListener('DOMContentLoaded', function() {
  // Add copy notification
  const showCopyNotification = (button) => {
    const original = button.innerHTML;
    button.innerHTML = '✓ Copied!';
    button.style.backgroundColor = '#4caf50';
    
    setTimeout(() => {
      button.innerHTML = original;
      button.style.backgroundColor = '';
    }, 2000);
  };

  // Enhanced code copy
  document.querySelectorAll('.md-clipboard').forEach(button => {
    button.addEventListener('click', function() {
      showCopyNotification(this);
    });
  });

  // Add anchor links to headings
  document.querySelectorAll('h2, h3, h4').forEach(heading => {
    if (heading.id) {
      const link = document.createElement('a');
      link.className = 'headerlink';
      link.href = '#' + heading.id;
      link.innerHTML = '#';
      link.style.marginLeft = '0.5rem';
      link.style.opacity = '0';
      link.style.transition = 'opacity 0.2s';
      
      heading.appendChild(link);
      
      heading.addEventListener('mouseenter', () => {
        link.style.opacity = '0.5';
      });
      
      heading.addEventListener('mouseleave', () => {
        link.style.opacity = '0';
      });
      
      link.addEventListener('mouseenter', () => {
        link.style.opacity = '1';
      });
    }
  });

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href !== '#') {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      }
    });
  });

  // Add external link indicators
  document.querySelectorAll('a[href^="http"]').forEach(link => {
    if (!link.hostname.includes('quantumforge.ai')) {
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
      
      // Add external link icon
      const icon = document.createElement('span');
      icon.innerHTML = ' ↗';
      icon.style.fontSize = '0.8em';
      icon.style.opacity = '0.6';
      link.appendChild(icon);
    }
  });

  // Table of contents highlight
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.8
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        document.querySelectorAll('.md-nav__link').forEach(link => {
          link.classList.remove('md-nav__link--active');
        });
        const activeLink = document.querySelector(`.md-nav__link[href="#${id}"]`);
        if (activeLink) {
          activeLink.classList.add('md-nav__link--active');
        }
      }
    });
  }, observerOptions);

  document.querySelectorAll('h2[id], h3[id]').forEach(heading => {
    observer.observe(heading);
  });

  // Search analytics (if Google Analytics is configured)
  if (typeof gtag !== 'undefined') {
    const searchInput = document.querySelector('.md-search__input');
    if (searchInput) {
      searchInput.addEventListener('blur', function() {
        if (this.value) {
          gtag('event', 'search', {
            search_term: this.value
          });
        }
      });
    }
  }

  // Add reading time estimator
  const content = document.querySelector('.md-content article');
  if (content) {
    const text = content.textContent;
    const wordCount = text.trim().split(/\s+/).length;
    const readingTime = Math.ceil(wordCount / 200); // Average reading speed
    
    const meta = document.querySelector('.md-content__inner');
    if (meta && readingTime > 1) {
      const timeTag = document.createElement('p');
      timeTag.className = 'reading-time';
      timeTag.innerHTML = `📖 ${readingTime} min read`;
      timeTag.style.color = '#666';
      timeTag.style.fontSize = '0.9em';
      timeTag.style.marginBottom = '1rem';
      meta.insertBefore(timeTag, meta.firstChild);
    }
  }

  // Dark mode toggle custom behavior
  const observer2 = new MutationObserver(() => {
    const isDark = document.body.getAttribute('data-md-color-scheme') === 'slate';
    // Store preference
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  });

  observer2.observe(document.body, {
    attributes: true,
    attributeFilter: ['data-md-color-scheme']
  });

  console.log('QuantumForge Docs loaded successfully! 🚀');
});

