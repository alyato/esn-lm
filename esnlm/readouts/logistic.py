""" This module defines the different nodes used to construct 
    hierarchical language models"""

import numpy as np
from esnlm.utils import softmax
from esnlm.optimization import newton_raphson, gradient, hessian

class LogisticRegression:
    """ Class for the multivariate logistiv regression.
        
        Parameters
        ----------
        input_dim : an integer corresponding to the number of features in input.
        output_dim : an integer corresponding to the number of classes.
        
        Notes
        -----
        The model is trained by minimizing a cross-entropy function. The target 
        can be binary (one-hot) vectors or have continuous value. This allows to use the 
        LOgisticRegression node as a component of a Mixture of Experts (MoE) model.
        """
        
        
    def __init__(self, input_dim, output_dim, verbose=True):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.verbose = verbose
        
        self.params = 3*(-1 + 2*np.random.rand(input_dim, output_dim))/np.sqrt(input_dim)
        
    def py_given_x(self, x):
        """ Returns the conditional probability of y given x
            
            Parameters
            ----------
            x : array of shape nb_samples*input_dim
            
            Returns
            -------
            y : array of shape nb_samples*output_dim with class probability components 
        """
        return softmax(np.dot(x, self.params))
    
    def log_likelihood(self, x, y):
        """ Compute the log-likelihood of the data {x,y} according to the current
            parameters of the model.
            
            Parameters
            ----------
            x : array of shape nb_samples*input_dim
            y : array of shape nb_samples*output_dim with one-hot row components
            
            Returns
            -------
            ll : the log-likelihood
        """
        post = self.py_given_x(x)
        lik = np.prod(post**y, axis=1)
        return np.sum(np.log(lik+1e-7))
    
    def sample_y_given_x(self, x):
        """ Generate of sample for each row of x according to P(Y|X=x).
            
            Parameters
            ----------
            x : array of shape nb_samples*input_dim
            
            Returns
            -------
            y : array of shape nb_samples*output_dim with one-hot row vectors
        """
        post = self.py_given_x(x)
        y = np.array([np.random.multinomial(1, post[i, :]) for i in range(x.shape[0])])
        return y
    
    def fit(self, x, y, method='Newton-Raphson', max_iter=20):
        """ Learn the parameters of the model, i.e. self.params.
        
        Parameters
        ----------
        x : array of shape nb_samples*nb_features
        y : array of shape nb_samples*output_dim
        method : string indicating the type of optimization
            - 'Newton-Raphson'
        nb_iter : the maximum number of iterations
        
        Returns
        -------
        params : the matrix of parameters 
        
        Examples
        --------
            >>> from esnlm.nodes import LogisticRegression
            >>> x = np.array([[1., 0.],[0., 1]]
            >>> y = np.array([[0., 1.],[1., 0]]
            >>> params = LogisticRegression(2,2).fit(x, y)
        """
        if type(y) == type([]):
            y = np.eye(self.output_dim)[y]
        
        def _objective_function(params):
            py_given_x = softmax(np.dot(x, params.reshape(self.params.shape)))
            lik = np.prod(py_given_x**y, axis=1)
            return np.sum(np.log(lik+1e-7))
        
        params = np.array(self.params)
        old_value = _objective_function(params)
        
        if method == 'Newton-Raphson':
            print "... Newton-Raphson:",
            for i in range(max_iter):
                if self.verbose == True:
                    print i,
                
                post = softmax(np.dot(x, params))
                grad = gradient(x, y, post, np.ones((y.shape[0], )))
                hess = hessian(x, y, post, np.ones((y.shape[0], )))
        
                params = newton_raphson(grad, hess, params, _objective_function)
            
                new_value = _objective_function(params)
                if new_value < old_value + 1:
                    break
                old_value = new_value
            
            self.params = params.reshape(self.params.shape)
            if self.verbose == True:
                print "The End."
        
        else:
            from scipy.optimize import minimize
            
            def obj(params):
                return -_objective_function(params)
                
            def grd(params):
                post = softmax(np.dot(x, params.reshape(self.params.shape)))
                return -gradient(x, y, post, np.ones((y.shape[0], ))).squeeze()
            
            def hsn(params):
                post = softmax(np.dot(x, params.reshape(self.params.shape)))
                return -hessian(x, y, post, np.ones((y.shape[0], )))
            
            params = params.reshape(params.size)
            res = minimize(obj, params,jac=grd, hess=hsn, method=method, 
                           options={'maxiter':100, 'xtol': 1e-4, 'disp': True})
            params = res.x
            self.params = params.reshape(self.params.shape)
        
        return params
            
            