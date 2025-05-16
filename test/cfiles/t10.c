#include <stdio.h>
#include <stdlib.h>

#define V 6


void addEdge(int adj[][V], int u, int v) {
    adj[u][v] = 1;
}

 (DFS)
void topologicalSortUtil(int adj[][V], int v, int visited[], int stack[], int* stackIndex) {
    visited[v] = 1;

    for (int i = 0; i < V; i++) {
        if (adj[v][i] && !visited[i]) {
            topologicalSortUtil(adj, i, visited, stack, stackIndex);
        }
    }

    stack[(*stackIndex)++] = v;
}


void topologicalSort(int adj[][V]) {
    int visited[V] = {0};
    int stack[V];
    int stackIndex = 0;

    for (int i = 0; i < V; i++) {
        if (!visited[i]) {
            topologicalSortUtil(adj, i, visited, stack, &stackIndex);
        }
    }

    printf("拓扑排序结果：\n");
    for (int i = stackIndex - 1; i >= 0; i--) {
        printf("%d ", stack[i]);
    }
    printf("\n");
}

int main() {
    int adj[V][V] = {0};


    addEdge(adj, 5, 2);
    addEdge(adj, 5, 0);
    addEdge(adj, 4, 0);
    addEdge(adj, 4, 1);
    addEdge(adj, 2, 3);
    addEdge(adj, 3, 1);

    topologicalSort(adj);

    return 0;
}