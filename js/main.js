(function () {
  "use strict";

  const COFFEE_THEME = {
    background: "transparent",
    font: '"Lato", -apple-system, BlinkMacSystemFont, sans-serif',
    title: {
      font: '"Playfair Display", Georgia, serif',
      fontSize: 18,
      fontWeight: 700,
      color: "#2A1B14",
      anchor: "start",
      offset: 12,
      subtitleFont: '"Lato", sans-serif',
      subtitleFontSize: 13,
      subtitleColor: "#5C463A",
    },
    axis: {
      labelFont: '"Lato", sans-serif',
      labelFontSize: 12,
      labelColor: "#5C463A",
      titleFont: '"Lato", sans-serif',
      titleFontSize: 12,
      titleFontWeight: 700,
      titleColor: "#2A1B14",
      domainColor: "#E2D6BD",
      tickColor: "#E2D6BD",
      gridColor: "#EFE6D2",
      gridOpacity: 0.6,
    },
    legend: {
      labelFont: '"Lato", sans-serif',
      labelFontSize: 12,
      titleFont: '"Lato", sans-serif',
      titleFontSize: 12,
      titleFontWeight: 700,
      labelColor: "#2A1B14",
      titleColor: "#2A1B14",
    },
    view: { stroke: "transparent" },
    range: {
      category: [
        "#2F5D50",
        "#A53F2B",
        "#6F4E37",
        "#1F5F5B",
        "#C9A87C",
        "#8C7361",
      ],
    },
    signals: [
      { name: "arabicaColor", value: "#2F5D50" },
      { name: "robustaColor", value: "#A53F2B" },
      { name: "accentCool", value: "#1F5F5B" },
      { name: "accentWarm", value: "#A53F2B" },
    ],
  };

  // Chart manifest
  const CHARTS = [
    { id: "vis-01", spec: "js/01_world_map.vl.json" },
    { id: "vis-02", spec: "js/02_top_producers.vl.json" },
    { id: "vis-03", spec: "js/03_import_trend.vl.json" },
    { id: "vis-04", spec: "js/04_arabica_robusta.vl.json" },
    { id: "vis-05", spec: "js/05_au_states.vl.json" },
    { id: "vis-06", spec: "js/06_per_capita.vl.json" },
    { id: "vis-07", spec: "js/07_city_bubbles.vl.json" },
    { id: "vis-08", spec: "js/08_imports_vs_price.vl.json" },
    { id: "vis-09", spec: "js/09_flow_map.vl.json" },
    { id: "vis-10", spec: "js/10_seasonality.vl.json" },
    { id: "vis-11", spec: "js/11_cpi.vl.json" },
    { id: "vis-12", spec: "js/12_five_cities.vl.json" },
  ];

  // Loader
  function loadChart(entry) {
    const el = document.getElementById(entry.id);
    if (!el) return;

    // Fetch the spec JSON, merge theme, embed.
    fetch(entry.spec)
      .then(function (r) {
        if (!r.ok) throw new Error("404: " + entry.spec);
        return r.json();
      })
      .then(function (spec) {
        // Remove placeholder text once we're rendering
        const ph = el.querySelector(".vis__placeholder");
        if (ph) ph.remove();

        spec.config = Object.assign({}, COFFEE_THEME, spec.config || {});
        spec.width = "container";
        spec.autosize = { type: "fit", contains: "padding", resize: true };

        return vegaEmbed("#" + entry.id, spec, {
          actions: false,
          renderer: "svg",
        });
      })
      .catch(function (err) {
        console.warn("[coffee] chart skipped:", entry.id, err.message);
      });
  }

  // IntersectionObserver
  function init() {
    if (typeof vegaEmbed !== "function") {
      console.warn("[coffee] vega-embed not loaded yet — retrying in 200ms");
      setTimeout(init, 200);
      return;
    }

    const obs = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          const id = e.target.id;
          const entry = CHARTS.find(function (c) {
            return c.id === id;
          });
          if (entry) {
            loadChart(entry);
            obs.unobserve(e.target);
          }
        });
      },
      { rootMargin: "200px 0px" },
    );

    CHARTS.forEach(function (c) {
      const el = document.getElementById(c.id);
      if (el) obs.observe(el);
    });
  }

  // Date stamp
  function stampDate() {
    const el = document.getElementById("hero-date");
    if (!el) return;
    const d = new Date();
    const months = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];
    el.textContent = months[d.getMonth()] + " " + d.getFullYear();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      stampDate();
      init();
    });
  } else {
    stampDate();
    init();
  }

  // Expose theme for inline use if someone wants to author specs inline
  window.CoffeeTheme = COFFEE_THEME;
})();
