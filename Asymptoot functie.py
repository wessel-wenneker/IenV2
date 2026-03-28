# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 00:53:29 2026

@author: wisse
"""
import numpy as np

def check_asymptote_sigma(sigma, n_check=50, sigma_tol=600, n_skip=1):
    left_sigma = sigma[n_skip:n_skip + n_check]
    right_sigma = sigma[-n_check-n_skip:-n_skip]

    left_problem = np.any(np.abs(left_sigma) > sigma_tol)
    right_problem = np.any(np.abs(right_sigma) > sigma_tol)

    if left_problem and right_problem:
        print("Asymptoot in buigspanningslijn aan beide uiteinden")
    elif left_problem:
        print("Asymptoot in buigspanningslijn links")
    elif right_problem:
        print("Asymptoot in buigspanningslijn rechts")
    else:
        print("Geen asymptoot in buigspanningslijn")

    return left_problem, right_problem

left_sigma, right_sigma = check_asymptote_sigma(sigma_dek_MPa)
left_sigma_b, right_sigma_b = check_asymptote_sigma(sigma_bodem_MPa)
    