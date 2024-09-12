import numpy as np
from utils import instgrad, generalized_projection

# Implementación en Python de SurvONS

# t0: Arreglo de tiempos iniciales de los individuos
# u: Arreglo de tiempos en los que los individuos experimentan el evento/son censurados (hat_T en R)
# delta: Arreglo de booleanos que indican si un individuo experimentó el evento o fue censurado
# X: Matriz con los vectores de características de cada uno de los individuos
# D: Diametro del espacio de las características
# gamma: Vector de valores de learning rate
# n: Número de iteraciones
# epsilon: Vector de valores de epsilon (epsilon_k = 1/(gamma_k * D) ^2)
# R: Matriz de los factores de riesgo de los individuos
# max0: Setea el valor de gamma_temp a 0

def surv_ons(t0, u, delta, X, D, gamma, n, epsilon, R, max0 = False):
    N = len(t0)
    d = np.shape(X)[1]  # entrega la segunda dimensión de X (número de características)
    K = len(gamma)

    beta = np.zeros((d, K))
    beta_arr = np.zeros((n, d, K))
    a_inv_arr = np.zeros((d, d, K))

    for i in range(0, K):
        a_inv_arr[:, :, i] = (1/epsilon[i]) * np.eye(d)

    pi_boa = np.full((K, 1), 1/K)
    pi_boa2 = pi_boa

    beta_boa_arr = np.zeros((n, d))
    grad_boa = np.zeros((n, d))
    grad_boa_hat = np.zeros((n, d, K))
    pi_boa_arr = np.zeros((n, K))
    lik_boa = np.zeros((n, 1))
    gamma_temp = np.zeros((n, 1))

    for t in range(1, n): # la iteración 0 da todo 0 => mata todo
        print(f"iteracion {t}")
        beta_boa = np.matmul(beta, pi_boa)
        grad_boa[t], hess_boa , lik_boa[t] = instgrad(t, t0, u, delta, X, beta_boa, R[t])

        norm_grad_boa = np.linalg.norm(grad_boa[t])
        algo = np.matmul(np.transpose(grad_boa[t]), hess_boa)
        mu = np.matmul(algo, grad_boa[t]) / max(1e-9, norm_grad_boa**4)

        gamma_t = 2*((-1/mu)*np.log(1 + mu*norm_grad_boa*D) + norm_grad_boa*D) / (max(1e-9, norm_grad_boa * D) ** 2)
        if (max0):
            gamma_t = 0
        gamma_temp[t] = gamma_t

        for i in range(0, K):
            beta_arr[t, :, i] = beta[:, i]
            
            gamma_max = max(gamma_t/4, gamma[i])

            grad_hat = grad_boa[t] * (1 + gamma_max * np.matmul(np.transpose(grad_boa[t]), beta[:, i]- beta_boa))
            grad_boa_hat[t,:,i] = grad_hat
            
            a_inv  = np.full((d,d), a_inv_arr[:,:,i])
            temp = a_inv @ grad_hat
            temp2 = np.outer(temp, temp.T) # es una matriz simétrica -> (1,3) == (3,1) y su diagonal con valores distintos

            a_inv = a_inv - (temp2/(1+ np.matmul(grad_hat.T, temp)))
            a_inv_arr[:,:,i] = a_inv
            
            beta[:,i] -= gamma[i]**-1 * np.matmul(a_inv, grad_hat)


            if (np.sqrt(np.matmul(np.transpose(beta[:,i]), beta[:,i])) > D):
                beta[:, i] = generalized_projection(a_inv, beta[:, i], D, d)

        term1 = np.dot(gamma, (np.matmul(np.transpose(grad_boa[t]), beta-np.matmul(beta_boa, np.transpose(np.ones((K, 1)))))))
        
        # revisar si es necesario maximum y minimum, o si sirve max y min -> sirve maximum
        pi_boa2 = np.exp(np.maximum(-100, np.minimum(100, np.log(pi_boa2) - term1 - term1**2)))
        pi_boa2 /= np.sum(pi_boa2)

        gamma_dot_pb2 = np.array([gamma]).T * pi_boa2
        pi_boa = gamma_dot_pb2 / np.sum(gamma_dot_pb2)

        if(t < n):
            beta_boa_arr[t] = (np.matmul(beta, pi_boa)).flatten()
            pi_boa_arr[t] = pi_boa.flatten()
    
    return [beta_arr, beta_boa_arr, pi_boa_arr, 
            lik_boa, gamma_temp, grad_boa, grad_boa_hat]