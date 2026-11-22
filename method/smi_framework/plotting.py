"""One frame for every plot page, in the format of the article's figures. Every style value of the plots lives here.

Values read from the current pages: font STIXGeneral with STIX mathematics at 9 pt, page 234 pt wide, frame margins 48, 8, 8, 34 pt, frame 119 pt high,
strokes 0.8 pt for the frame and ticks, 0.6 pt for the grid, 1.2 pt for the curves. The journal's minimums are 8 pt for text outside scripts and 0.28 pt for strokes.
"""
import matplotlib

matplotlib.use('pdf')
from matplotlib import pyplot as plt  # noqa: E402

PAGE_W, LEFT, RIGHT, TOP, BOTTOM, AX_H = 234.0, 48.0, 8.0, 8.0, 34.0, 119.0
LINE_W, FRAME_W, GRID_W = 1.2, 0.8, 0.6
STYLE = {'font.family': 'STIXGeneral', 'mathtext.fontset': 'stix', 'font.size': 9, 'axes.labelsize': 9, 'xtick.labelsize': 9, 'ytick.labelsize': 9,
         'legend.fontsize': 9, 'lines.scale_dashes': False, 'pdf.fonttype': 42, 'axes.linewidth': FRAME_W, 'xtick.major.width': FRAME_W, 'ytick.major.width': FRAME_W,
         'xtick.direction': 'in', 'ytick.direction': 'in', 'grid.linewidth': GRID_W, 'lines.linewidth': LINE_W, 'axes.unicode_minus': True}


def aiaa_axes(xlabel, ylabel, xlim, ylim, xticks=None, yticks=None, legend_h=31.0):
    """A figure and axes on the frame of the article: one panel per page, the legend in the `legend_h` points below the frame."""
    plt.rcParams.update(STYLE)
    page_h = TOP + AX_H + BOTTOM + legend_h
    fig = plt.figure(figsize=(PAGE_W / 72.0, page_h / 72.0))
    ax = fig.add_axes([LEFT / PAGE_W, (BOTTOM + legend_h) / page_h, (PAGE_W - LEFT - RIGHT) / PAGE_W, AX_H / page_h])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    if xticks is not None:
        ax.set_xticks(xticks)
    if yticks is not None:
        ax.set_yticks(yticks)
    ax.grid(True, which='major')
    return fig, ax


def legend_below(fig, ax, ncol=2):
    """The legend under the frame, on one block, with no box."""
    h, lab = ax.get_legend_handles_labels()
    fig.legend(h, lab, loc='lower center', ncol=ncol, frameon=False, handlelength=2.0, columnspacing=1.0, borderaxespad=0.0, labelspacing=0.2)
