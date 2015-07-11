from env import *
def test():
  ctx = Context()
  sw0 = LinkStateSwitch("sw0", ctx)
  c0 = Controller("c0", ctx, "c0")
  l0 = Link(ctx, c0, sw0)
  def schedUp():
    l0.SetUp()
  ctx.schedule_task(1, schedUp)
  ctx.run()
if __name__ == "__main__":
  print "Runnning test"
  test()
