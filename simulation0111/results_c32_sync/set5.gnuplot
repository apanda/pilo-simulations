# Note you need gnuplot 4.4 for the pdfcairo terminal.

set terminal pdfcairo font "Gill Sans, 16" linewidth 6 rounded dashed

# Line style for axes
set style line 80 lt rgb "#808080"

# Line style for grid
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"  # grey

#set grid back linestyle 81
set border 3 back linestyle 80 # Remove border on top and right.  These
# borders are useless and make it harder to see plotted lines near the border.
# Also, put it in grey; no need for so much emphasis on a border.

set xtics nomirror
set ytics nomirror

#set ylabel "# of Storage Nodes"
#set xlabel "# of Disks in Compute Node"
#set bars small
#set datafile separator ","
#set output "storage.pdf"
#plot "data_for_graph_10" index 0 using 1:2 w linespoints lc -1 lt 1 lw 1 title "10 Gbps",\
     #"data_for_graph_10" index 1 using 1:2 w linespoints lc 9 lt 0 lw 1 pt 3 title "40 Gbps"
# perturb min p5 p50 p95 max mean var
set ylabel  "Reachability"
set xlabel "Perturbation"
set xrange [:1050] reverse
set output "reachability_percentile5.pdf"
plot "set5.ele" using 1:4:3:5 w yerrorbars pt 4 lc 0 lt -1 title "ELE",\
      "set5.ele" using 1:4 w lines lc 0 lt -1 notitle,\
     "set5.gos" using 1:4:3:5 w yerrorbars lc 3 lt 2 title "Gossip",\
     "set5.gos" using 1:4 w lines lc 3 lt 2 notitle,\
     "set5.paxos" using 1:4:3:5 w yerrorbars lc 9 lt 10 title "Paxos", \
     "set5.paxos" using 1:4 w lines lc 9 lt 10 notitle
reset

# Note you need gnuplot 4.4 for the pdfcairo terminal.

set terminal pdfcairo font "Gill Sans, 16" linewidth 6 rounded dashed

# Line style for axes
set style line 80 lt rgb "#808080"

# Line style for grid
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"  # grey

#set grid back linestyle 81
set border 3 back linestyle 80 # Remove border on top and right.  These
# borders are useless and make it harder to see plotted lines near the border.
# Also, put it in grey; no need for so much emphasis on a border.

set xtics nomirror
set ytics nomirror

#set ylabel "# of Storage Nodes"
#set xlabel "# of Disks in Compute Node"
#set bars small
#set datafile separator ","
#set output "storage.pdf"
#plot "data_for_graph_10" index 0 using 1:2 w linespoints lc -1 lt 1 lw 1 title "10 Gbps",\
     #"data_for_graph_10" index 1 using 1:2 w linespoints lc 9 lt 0 lw 1 pt 3 title "40 Gbps"
# perturb min p5 p50 p95 max mean var
set ylabel  "Reachability"
set xlabel "Perturbation"
set xrange [:1050] reverse
set yrange [:100]
set output "reachability_mean5.pdf"
plot "set5.ele" using 1:7:(1.96 * sqrt($8)) w yerrorbars pt 4 lc 0 lt -1 title "ELE",\
     "set5.ele" using 1:7:(1.96 * sqrt($8)) w lines lc 0 lt -1 notitle,\
     "set5.gos" using 1:7:(1.96 * sqrt($8)) w yerrorbars lc 3 lt 2 title "Gossip",\
     "set5.gos" using 1:7:(1.96 * sqrt($8)) w l lc 3 lt 2 notitle,\
     "set5.paxos" using 1:7:(1.96*sqrt($8)) w yerrorbars lc 9 lt 10 title "Paxos", \
     "set5.paxos" using 1:7:(1.96*sqrt($8)) w l lc 9 lt 10 notitle

