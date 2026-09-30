import { useEffect, useState } from 'react';

export function useAsync<T>(load: () => Promise<T>, dependencies: unknown[]) {
  const [state, setState] = useState<{data:T|null;error:string;loading:boolean}>({data:null,error:'',loading:true});
  useEffect(() => {
    let active = true;
    setState({data:null,error:'',loading:true});
    load().then(data => active && setState({data,error:'',loading:false}))
      .catch(error => active && setState({data:null,error:error?.message || 'Request failed',loading:false}));
    return () => { active = false; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
  return state;
}
