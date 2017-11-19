
// g++ game_of_life.cc -o game_of_life -std=c++11 -O3

#include <array>
#include <iostream>
#include <ostream>
#include <sstream>
#include <string>
#include <vector>
#include <sys/ioctl.h>
#include <stdio.h>
#include <unistd.h>


std::array<int[2], 8> NEIGHBORS = {{
    {-1, -1}, {-1, 0}, {-1, 1},
    { 0, -1},          { 0, 1},
    { 1, -1}, { 1, 0}, { 1, 1},
}};

std::array<int[2], 9> RULES = {{
  {0, 0},  // 0
  {0, 0},  // 1
  {0, 1},  // 2, dead, alive
  {1, 1},  // 3, dead, alive
  {0, 0},  // 4
  {0, 0},  // 5
  {0, 0},  // 6
  {0, 0},  // 7
  {0, 0},  // 8
}};

char OUT_CHARS[3] = " #";


class State {
 public:
  State(int height, int width) : 
    cur_(0), height_(height), width_(width), state_(height * width * 2) {
    randomize();
  }

  void randomize() {
    for (int i = 0; i < height_; i++) {
      for (int j = 0; j < width_; j++) {
        get(i, j) = rand() % 2;
      }
    }
  }

  std::string to_str() {
    std::stringstream out;
    out << "+" << std::string(width_, '-') << "+\n";
    for (int i = 0; i < height_; i++) {
      out << "|";
      for (int j = 0; j < width_; j++) {
        out << OUT_CHARS[get(i, j)];
      }
      out << "|\n";
    }
    out << "+" << std::string(width_, '-') << "+\n";
    return out.str();
  }

  void update() {
    for (int i = 0; i < height_; i++) {
      for (int j = 0; j < width_; j++) {
        int count = 0;
        for (int k = 0; k < 8; k++) {
          count += get((i + NEIGHBORS[k][0] + height_) % height_,
                       (j + NEIGHBORS[k][1] + width_) % width_);
        }
        get(i, j, true) = RULES[count][get(i, j)];
      }
    }
    cur_ = !cur_;
  }

  char& get(int y, int x, bool flip=false) {
    return state_[((cur_ ^ flip) * height_ * width_) + 
                  (width_ * y) + x];
  }

 private:
  bool cur_;
  int height_;
  int width_;
  std::vector<char> state_;
};


int main() {
  struct winsize w;
  ioctl(STDOUT_FILENO, TIOCGWINSZ, &w);

  State state(w.ws_row - 3, w.ws_col - 2);

  std::cout.setf(std::ios::unitbuf);
  while(true) {
      std::cout << state.to_str() << std::flush;
      state.update();
    }
}
