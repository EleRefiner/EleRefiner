for i in {0..99}
do
   python get_IoU.py $i &
done

wait

echo "所有进程执行完毕"