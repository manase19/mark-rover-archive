import engine
import chase
import opening

def main():
    game = engine.Game()
    first = opening.install(game, then=chase.begin)
    game.start(first, keys=("b", "Down"))

if __name__ == "__main__":
    main()