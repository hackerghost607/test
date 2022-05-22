#include <iostream>
using namespace std;

void pyramid(){




for (int i=5;i>=1;i--){
for(int j=i;j>0;j--){
cout<<j << " ";
}
cout<<endl;
}
}

 int main()
{ 
 for(int i=0;i<15;i++)
 cout<<" ";
 cout<<"M         M";
 cout<<endl;
 
 for(int j=0;j<13;j++)
 cout<<" ";
 cout<<"M   M     M   M";
 cout<<endl;

 for(int k=0;k<11;k++)
 cout<<" ";
 cout<<"*      *   *      *";
 cout<<endl;

 for(int l=0;l<11;l++)
 cout<<" ";
 cout<<"*       * *       *";
 cout<<endl;
 
 for(int m=0;m<11;m++)
 cout<<" ";
 cout<<"*        *        *";
 cout<<endl;
 
 for(int n=0;n<11;n++)
 cout<<" ";
 cout<<"*                 *";
 cout<<endl;
 
 for(int o=0;o<12;o++)
 cout<<" ";
 cout<<"*               *";
 cout<<endl; 

 for(int p=0;p<13;p++)
 cout<<" ";
 cout<<"*             *";
 cout<<endl;
 
 for(int q=0;q<14;q++)
 cout<<" ";
 cout<<"*           *";
 cout<<endl;
 
 for(int r=0;r<15;r++)
 cout<<" ";
 cout<<"*         *";
 cout<<endl;
 
 for(int s=0;s<17;s++)
 cout<<" ";
 cout<<"*     *";
 cout<<endl;
 
 for(int t=0;t<20;t++)
 cout<<" ";
 cout<<"**";
 cout<<endl;
 return 0;
}