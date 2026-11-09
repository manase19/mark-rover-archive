import turtle

import survivor_log_scene2 as scene2
import survivor_log_scene3 as scene3
import survivor_log as scene1

screen = turtle.Screen()
screen.setup(900, 600)

scenes = [
    scene1.play,
    scene2.play,
    scene3.play
]

def run_scene(index=0):
    screen.clear()

    if index >= len(scenes):
        screen.bye()
        return

    scenes[index](
        screen,
        lambda: run_scene(index + 1)
    )
def main():
    run_scene()
    screen.mainloop()

if __name__ == '__main__':
    main()