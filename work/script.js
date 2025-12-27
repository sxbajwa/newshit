// SONG FILES (order matters!)
const songs = [
  "../music/song1.mp3", // image1 → YOU
  "../music/song2.mp3", // image2 → song2
  "../music/song3.mp3", // image3 → song3
];

const player = document.getElementById("player");
let currentSong = -1;

// PLAY SONG
function playSong(index) {
  if (currentSong !== index) {
    currentSong = index;
    player.src = songs[index];
    player.play();
    highlightSong();
  }
}

// HIGHLIGHT ACTIVE SONG
function highlightSong() {
  document.querySelectorAll(".song-card").forEach((card, i) => {
    card.style.boxShadow =
      i === currentSong
        ? "0 0 25px rgba(255,105,180,0.8)"
        : "0 8px 20px rgba(0,0,0,0.12)";
  });
}

// LIKE BUTTON HEART POP
function like(event) {
  event.stopPropagation(); // VERY IMPORTANT
  const btn = event.currentTarget;

  const heart = document.createElement("span");
  heart.className = "heart";
  heart.innerText = "❤";
  btn.appendChild(heart);

  setTimeout(() => heart.remove(), 800);
}

// AUTO NEXT SONG
player.addEventListener("ended", () => {
  currentSong = (currentSong + 1) % songs.length;
  playSong(currentSong);
});
