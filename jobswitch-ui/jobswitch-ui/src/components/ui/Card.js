import React from 'react';

const Card = ({ children, className = '', ...props }) => {
  const classes = `rounded-lg border bg-card text-card-foreground shadow-sm bg-white border-gray-200 ${className}`;

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

const CardHeader = ({ children, className = '', ...props }) => {
  const classes = `flex flex-col space-y-1.5 p-6 ${className}`;

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

const CardTitle = ({ children, className = '', ...props }) => {
  const classes = `text-2xl font-semibold leading-none tracking-tight ${className}`;

  return (
    <h3 className={classes} {...props}>
      {children}
    </h3>
  );
};

const CardDescription = ({ children, className = '', ...props }) => {
  const classes = `text-sm text-muted-foreground text-gray-600 ${className}`;

  return (
    <p className={classes} {...props}>
      {children}
    </p>
  );
};

const CardContent = ({ children, className = '', ...props }) => {
  const classes = `p-6 pt-0 ${className}`;

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

const CardFooter = ({ children, className = '', ...props }) => {
  const classes = `flex items-center p-6 pt-0 ${className}`;

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };