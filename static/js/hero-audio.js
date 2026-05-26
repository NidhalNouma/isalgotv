(function () {
  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn, { once: true });
      return;
    }
    fn();
  }

  function loadHowler(cb) {
    if (
      typeof window.Howl !== "undefined" &&
      typeof window.Howler !== "undefined"
    ) {
      cb();
      return;
    }

    var existing = document.querySelector('script[data-hero-howler="1"]');
    if (existing) {
      existing.addEventListener("load", cb, { once: true });
      return;
    }

    var s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/howler@2.2.4/dist/howler.min.js";
    s.async = true;
    s.setAttribute("data-hero-howler", "1");
    s.addEventListener("load", cb, { once: true });
    document.head.appendChild(s);
  }

  function initHeroAudio(el) {
    var toggle = el.querySelector(".js-hero-audio-toggle");
    var wave = el.querySelector(".js-hero-audio-wave");
    var playIcon = el.querySelector(".js-hero-audio-icon-play");
    var pauseIcon = el.querySelector(".js-hero-audio-icon-pause");
    var src = el.getAttribute("data-audio-src");
    var labelPlay = el.getAttribute("data-label-play") || "Play audio preview";
    var labelPause =
      el.getAttribute("data-label-pause") || "Pause audio preview";
    var waveTheme = el.getAttribute("data-wave-theme") || "default";

    if (!toggle || !wave || !src || typeof window.Howl === "undefined") return;

    var waveCtx = wave.getContext("2d");
    if (!waveCtx) return;

    var rafId = 0;
    var isPlaying = false;
    var analyser = null;
    var freqData = null;
    var analyserReady = false;
    var fallbackPhase = 0;

    var heroSound = new Howl({
      src: [src],
      html5: false,
      loop: false,
      volume: 1,
    });

    function initAnalyser() {
      if (analyserReady || !window.Howler || !Howler.ctx || !Howler.masterGain)
        return;
      try {
        analyser = Howler.ctx.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.84;
        Howler.masterGain.connect(analyser);
        freqData = new Uint8Array(analyser.frequencyBinCount);
        analyserReady = true;
      } catch (e) {
        analyserReady = false;
      }
    }

    function barsGradient() {
      var g = waveCtx.createLinearGradient(0, 0, wave.width, 0);
      if (waveTheme === "yellow") {
        g.addColorStop(0, "#fef08a");
        g.addColorStop(0.5, "#facc15");
        g.addColorStop(1, "#eab308");
      } else {
        g.addColorStop(0, "#22d3ee");
        g.addColorStop(0.5, "#3b82f6");
        g.addColorStop(1, "#38bdf8");
      }
      return g;
    }

    function drawIdleBars() {
      waveCtx.clearRect(0, 0, wave.width, wave.height);
      var bars = 16;
      var gap = 3;
      var barW = (wave.width - gap * (bars - 1)) / bars;
      var idleH = 5;
      var y = (wave.height - idleH) / 2;
      waveCtx.fillStyle =
        waveTheme === "yellow"
          ? "rgba(250,204,21,0.5)"
          : "rgba(59,130,246,0.5)";
      for (var i = 0; i < bars; i++) {
        var x = i * (barW + gap);
        waveCtx.fillRect(x, y, barW, idleH);
      }
    }

    function drawBars() {
      if (!isPlaying) return;

      waveCtx.clearRect(0, 0, wave.width, wave.height);
      var bars = 16;
      var gap = 3;
      var barW = (wave.width - gap * (bars - 1)) / bars;
      var mid = wave.height / 2;

      waveCtx.fillStyle = barsGradient();

      if (analyserReady && analyser && freqData) {
        analyser.getByteFrequencyData(freqData);
      }

      for (var i = 0; i < bars; i++) {
        var x = i * (barW + gap);
        var h;

        if (analyserReady && analyser && freqData) {
          var start = Math.floor((i / bars) * freqData.length);
          var end = Math.max(
            start + 1,
            Math.floor(((i + 1) / bars) * freqData.length),
          );
          var total = 0;
          var count = 0;
          for (var b = start; b < end; b++) {
            total += freqData[b];
            count += 1;
          }
          var avg = count ? total / count : 0;
          h = 4 + (avg / 255) * (wave.height - 8);
        } else {
          var pulse = Math.sin(fallbackPhase * 0.11 + i * 0.9) * 0.5 + 0.5;
          var detail = Math.sin(fallbackPhase * 0.18 + i * 1.7) * 0.5 + 0.5;
          h = Math.max(
            4,
            Math.min(wave.height - 2, 8 * (0.6 + pulse * 0.9 + detail * 0.45)),
          );
        }

        var y = mid - h / 2;
        waveCtx.fillRect(x, y, barW, h);
      }

      fallbackPhase += 3;
      rafId = requestAnimationFrame(drawBars);
    }

    function setPlayingUI(playing) {
      isPlaying = playing;
      toggle.setAttribute("aria-pressed", String(playing));
      toggle.setAttribute("aria-label", playing ? labelPause : labelPlay);
      if (playIcon && pauseIcon) {
        playIcon.classList.toggle("hidden", playing);
        pauseIcon.classList.toggle("hidden", !playing);
      }
      cancelAnimationFrame(rafId);
      if (playing) {
        drawBars();
      } else {
        drawIdleBars();
      }
    }

    drawIdleBars();

    toggle.addEventListener("click", function () {
      if (!heroSound.playing()) {
        if (window.Howler && Howler.ctx && Howler.ctx.state === "suspended") {
          Howler.ctx.resume().catch(function () {});
        }
        initAnalyser();
        heroSound.play();
      } else {
        heroSound.pause();
      }
    });

    heroSound.on("play", function () {
      initAnalyser();
      setPlayingUI(true);
    });

    heroSound.on("pause", function () {
      setPlayingUI(false);
    });

    heroSound.on("stop", function () {
      setPlayingUI(false);
    });

    heroSound.on("end", function () {
      setPlayingUI(false);
    });

    heroSound.on("loaderror", function () {
      setPlayingUI(false);
    });

    heroSound.on("playerror", function () {
      setPlayingUI(false);
    });
  }

  onReady(function () {
    loadHowler(function () {
      var nodes = document.querySelectorAll(".js-hero-audio");
      nodes.forEach(initHeroAudio);
    });
  });
})();
